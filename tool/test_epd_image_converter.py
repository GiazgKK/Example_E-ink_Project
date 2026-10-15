import tempfile
import unittest
from pathlib import Path
from PIL import Image
from epd_image_converter import auto_tone, convert, prepare_image, WIDTH, HEIGHT, PLANE_SIZE


class ConversionTests(unittest.TestCase):
    def test_contain_preserves_both_edges_of_wide_image(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wide.png"
            source = Image.new("RGB", (1200, 675), "black")
            source.paste((255, 0, 0), (0, 0, 90, 675))
            source.paste((0, 255, 0), (1110, 0, 1200, 675))
            source.save(path)
            prepared = prepare_image(path)
            self.assertEqual(prepared.getpixel((0, 150)), (255, 0, 0))
            self.assertEqual(prepared.getpixel((399, 150)), (0, 255, 0))
            self.assertEqual(prepared.getpixel((200, 0)), (255, 255, 255))

    def test_artwork_keeps_dark_red_and_pale_red_edges(self):
        image = Image.new("RGB", (WIDTH, HEIGHT), "white")
        image.putpixel((0, 0), (80, 10, 10))
        image.putpixel((1, 0), (255, 190, 190))
        image.putpixel((2, 0), (160, 90, 75))
        _, red, _ = convert(image, red_mode="artwork")
        self.assertEqual(red[0], 0xC0)

    def test_auto_lifts_dark_details_preserves_endpoints(self):
        gray = Image.new("L", (400, 300))
        gray.putdata([20 + (i % 160) for i in range(400*300)])
        corrected = auto_tone(gray)
        self.assertGreater(corrected.getpixel((60, 0)), gray.getpixel((60, 0)))
        solid = Image.new("L", (400, 300), 0)
        self.assertEqual(auto_tone(solid).getextrema(), (0, 0))
        self.assertEqual(auto_tone(Image.new("L", solid.size, 255)).getextrema(), (255, 255))

    def test_skin_is_not_red_and_red_can_be_disabled(self):
        image = Image.new("RGB", (WIDTH, HEIGHT), (160, 90, 75))
        _, red, _ = convert(image)
        self.assertFalse(any(red))
        image.paste((255, 0, 0), (0, 0, WIDTH, HEIGHT))
        _, red, _ = convert(image, red_mode="off")
        self.assertFalse(any(red))

    def test_color_polarity_and_bit_order(self):
        image = Image.new("RGB", (WIDTH, HEIGHT), "white")
        image.putpixel((0, 0), (0, 0, 0))
        image.putpixel((1, 0), (255, 0, 0))
        image.putpixel((399, 299), (0, 0, 0))
        black, red, preview = convert(image)
        self.assertEqual((len(black), len(red)), (PLANE_SIZE, PLANE_SIZE))
        self.assertEqual((black[0], red[0], black[-1]), (0x80, 0x40, 0x01))
        self.assertEqual(preview.getpixel((1, 0)), (255, 0, 0))
        self.assertTrue(all(not (b & r) for b, r in zip(black, red)))

    def test_dither_does_not_put_black_on_red(self):
        image = Image.new("RGB", (WIDTH, HEIGHT), (120, 120, 120))
        for x in range(200, 400):
            for y in range(HEIGHT):
                image.putpixel((x, y), (255, 0, 0))
        black, red, _ = convert(image, dither=True)
        self.assertTrue(all(not (b & r) for b, r in zip(black, red)))
        self.assertGreater(sum(b.bit_count() for b in black), 0)
        self.assertEqual(sum(r.bit_count() for r in red), 200 * HEIGHT)

    def test_transparency_and_resize_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.png"
            Image.new("RGBA", (100, 100), (255, 0, 0, 0)).save(path)
            for fit in ("contain", "crop", "stretch"):
                prepared = prepare_image(path, fit)
                self.assertEqual(prepared.size, (WIDTH, HEIGHT))
                self.assertEqual(prepared.getpixel((200, 150)), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
