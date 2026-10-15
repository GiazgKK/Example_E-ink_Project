"""Convert images to black/red/white 400x300 bitmaps for Example_Display_Image."""
import argparse
import math
import colorsys
import sys
from pathlib import Path

# Use the Pillow wheel matching this Python ABI; never mix native extensions
# built for different Python versions in the same import directory.
LOCAL_PACKAGES = (Path(__file__).resolve().parent / ".local-packages" /
                  f"py{sys.version_info.major}{sys.version_info.minor}")
if LOCAL_PACKAGES.is_dir():
    sys.path.insert(0, str(LOCAL_PACKAGES))

from PIL import Image, ImageDraw, ImageOps, ImageFilter

WIDTH, HEIGHT = 400, 300
PLANE_SIZE = WIDTH * HEIGHT // 8
DEFAULT_OUTPUT = (Path(__file__).resolve().parent.parent /
                  "include" / "image_data.h")


def prepare_image(path, fit="contain", rotate="none"):
    with Image.open(path) as source:
        rgba = ImageOps.exif_transpose(source).convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        image = background.convert("RGB")
    if rotate == "cw":
        image = image.rotate(-90, expand=True, resample=Image.Resampling.BICUBIC)
    elif rotate == "ccw":
        image = image.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    elif rotate == "180":
        image = image.rotate(180, expand=True)
    if fit == "crop":
        return ImageOps.fit(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    if fit == "stretch":
        return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    resized = ImageOps.contain(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    canvas.paste(resized, ((WIDTH - resized.width) // 2, (HEIGHT - resized.height) // 2))
    return canvas


def demo_image():
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 399, 299), outline="black", width=4)
    draw.text((24, 24), "GOOD DISPLAY 400 x 300", fill="black")
    draw.rectangle((25, 65, 185, 230), fill="black")
    draw.rectangle((215, 65, 375, 230), fill=(255, 0, 0))
    draw.text((25, 250), "BLACK", fill="black")
    draw.text((215, 250), "RED", fill=(255, 0, 0))
    return image


def auto_tone(gray, brightness=1.0):
    """Lift photographic midtones, retaining true black and white endpoints."""
    histogram = gray.histogram()
    # Ignore near-black backdrop and white padding when estimating exposure.
    count = sum(histogram[20:245])
    if not count:
        return gray.point(lambda v: min(255, round(v * brightness)))

    def percentile(fraction):
        total = 0
        for value in range(20, 245):
            total += histogram[value]
            if total >= count * fraction:
                return value
        return 244

    # Avoid turning uniform gray images into solid white.
    high = max(200, percentile(0.98))
    middle = min(0.95, max(0.05, percentile(0.50) / high))
    gamma = min(1.0, max(0.45, math.log(0.60) / math.log(middle)))
    lut = [min(255, round(255 * min(1.0, v / high) ** gamma * brightness))
           for v in range(256)]
    return gray.point(lut).filter(ImageFilter.UnsharpMask(radius=1, percent=110, threshold=3))


def convert(image, black_threshold=160, red_min=70, red_margin=40, dither=True,
            auto=True, brightness=1.0, red_mode="strict"):
    """Row major, MSB first, 1 = ink; black and red never overlap."""
    if image.size != (WIDTH, HEIGHT):
        raise ValueError("Image must be 400x300; resize using prepare_image first")
    red_mask, luminance = [], []
    for r, g, b in image.getdata():
        is_red = r >= red_min and r - max(g, b) >= red_margin
        if red_mode in ("strict", "artwork"):
            hue, saturation, _ = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hue_distance = min(hue, 1 - hue) * 360
            # HSV hue separates red from orange/skin. Artwork additionally
            # retains pale red antialiased lettering on a white background.
            is_red = (r >= red_min and hue_distance <= 8 and
                      saturation >= (0.20 if red_mode == "artwork" else 0.55))
        elif red_mode == "off":
            is_red = False
        red_mask.append(is_red)
        luminance.append(round(0.299*r + 0.587*g + 0.114*b))
    gray = Image.new("L", image.size)
    gray.putdata(luminance)
    if auto:
        gray = auto_tone(gray, brightness)
    elif brightness != 1.0:
        gray = gray.point(lambda v: min(255, round(v * brightness)))
    # Mask red after exposure estimation so it doesn't bias the histogram.
    gray.putdata([255 if red else value for value, red in zip(gray.getdata(), red_mask)])
    if dither:
        gray = gray.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    black, red, colors = bytearray(PLANE_SIZE), bytearray(PLANE_SIZE), []
    for i, (value, is_red) in enumerate(zip(gray.getdata(), red_mask)):
        mask = 0x80 >> (i % 8)
        if is_red:
            red[i // 8] |= mask
            colors.append((255, 0, 0))
        elif value < (128 if dither else black_threshold):
            black[i // 8] |= mask
            colors.append((0, 0, 0))
        else:
            colors.append((255, 255, 255))
    preview = Image.new("RGB", image.size)
    preview.putdata(colors)
    return bytes(black), bytes(red), preview


def write_header(path, black, red):
    lines = ["// Generated: 400x300, MSB first, 1 = ink.", "#pragma once", "#include <Arduino.h>", ""]
    for name, plane in (("image_black", black), ("image_red", red)):
        lines.append(f"const uint8_t {name}[{len(plane)}] PROGMEM = {{")
        for offset in range(0, len(plane), 16):
            lines.append("    " + ", ".join(f"0x{x:02X}" for x in plane[offset:offset+16]) + ",")
        lines.extend(["};", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def byte_value(value):
    number = int(value)
    if not 0 <= number <= 255:
        raise argparse.ArgumentTypeError("Value must be between 0 and 255")
    return number


def brightness_value(value):
    number = float(value)
    if not math.isfinite(number) or not 0.5 <= number <= 2.0:
        raise argparse.ArgumentTypeError("Brightness must be between 0.5 and 2.0")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fit", choices=("contain", "crop", "stretch"), default="contain",
                        help="contain keeps the entire image with white padding (default)")
    parser.add_argument("--rotate", choices=("none", "cw", "ccw", "180"), default="none",
                        help="rotate source before fitting: cw/ccw = 90 degrees; default: none")
    parser.add_argument("--black-threshold", type=byte_value, default=160)
    parser.add_argument("--red-min", type=byte_value, default=70)
    parser.add_argument("--red-margin", type=byte_value, default=40)
    parser.add_argument("--dither", action=argparse.BooleanOptionalAction, default=True,
                        help="Dither black/white layer (default: enabled)")
    parser.add_argument("--auto", action=argparse.BooleanOptionalAction, default=True,
                        help="Automatic exposure and detail enhancement (default: enabled)")
    parser.add_argument("--brightness", type=brightness_value, default=1.0)
    parser.add_argument("--red-mode", choices=("strict", "artwork", "off", "legacy"), default="strict",
                        help="strict: photos; artwork: red lettering; off: monochrome")
    args = parser.parse_args()
    if (args.input is None) == (not args.demo):
        parser.error("Provide an input image OR --demo")
    try:
        image = demo_image() if args.demo else prepare_image(args.input, args.fit, args.rotate)
        prepared_path = args.output.with_name(args.output.stem + "_prepared.png")
        prepared_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(prepared_path)
        black, red, preview = convert(image, args.black_threshold, args.red_min, args.red_margin,
                                      args.dither, args.auto, args.brightness, args.red_mode)
        write_header(args.output, black, red)
        preview_path = args.output.with_name(args.output.stem + "_preview.png")
        preview.save(preview_path)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Conversion failed: {error}\n")
    print(f"Header: {args.output.resolve()}")
    print(f"Preview: {preview_path.resolve()}")
    print(f"Resized original before color conversion: {prepared_path.resolve()}")
    print(f"Fit: {args.fit}; rotate: {args.rotate}; screen output: {WIDTH}x{HEIGHT}")
    if args.fit == "crop":
        print("WARNING: --fit crop removes image edges. Use --fit contain to keep everything.")
    print(f"Each plane: {PLANE_SIZE} bytes; total: {len(black)+len(red)} bytes")
    print(f"Auto: {args.auto}; dither: {args.dither}; red mode: {args.red_mode}")
    print(f"Black coverage: {100 * sum(v.bit_count() for v in black) / (WIDTH*HEIGHT):.1f}%")


if __name__ == "__main__":
    main()
