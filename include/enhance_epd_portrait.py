from pathlib import Path
from PIL import Image, ImageDraw

folder = Path(__file__).parent
image = Image.open(folder / "image_data_prepared.png").convert("RGB")
draw = ImageDraw.Draw(image)
ink = (18, 20, 24)
red = (210, 35, 48)
paper = (255, 255, 255)

# Reinforce the extended index finger, raised finger and finger joints.
draw.line([(48, 156), (53, 133), (57, 107), (59, 82), (63, 70),
           (70, 71), (76, 86), (77, 111), (75, 135)], fill=ink, width=2, joint="curve")
draw.line([(91, 143), (112, 137), (135, 130), (155, 129), (167, 134),
           (171, 141), (168, 148), (156, 152), (133, 151), (111, 157)],
          fill=ink, width=2, joint="curve")
draw.line([(27, 174), (43, 158), (57, 151), (76, 151), (96, 157), (112, 165)],
          fill=ink, width=2, joint="curve")
draw.line([(30, 187), (47, 174), (61, 169), (82, 171), (101, 179)],
          fill=ink, width=2, joint="curve")
draw.line([(47, 197), (60, 186), (76, 184), (91, 190)], fill=ink, width=2, joint="curve")
# Fingernails and crease marks.
draw.ellipse((151, 134, 163, 143), outline=ink, width=2)
draw.arc((60, 72, 72, 85), 185, 330, fill=ink, width=2)
draw.line([(66, 158), (71, 163), (76, 159)], fill=ink, width=2)
draw.line([(86, 174), (91, 179), (96, 176)], fill=ink, width=2)
draw.line([(59, 184), (64, 188), (69, 185)], fill=ink, width=2)

# Sharpen both visible Sharingan eyes with a clean iris, pupil and tomoe.
def sharingan(cx, cy, radius=5):
    draw.line([(cx-radius-5, cy), (cx-2, cy-radius-2),
               (cx+radius+4, cy), (cx+2, cy+radius+2),
               (cx-radius-5, cy)], fill=ink, width=2, joint="curve")
    draw.ellipse((cx-radius+1, cy-radius+1, cx+radius-1, cy+radius-1),
                 fill=red, outline=ink, width=1)
    draw.ellipse((cx-1, cy-1, cx+1, cy+1), fill=ink)
    for dx, dy in [(-4, -3), (4, -2), (1, 4)]:
        draw.ellipse((cx+dx-1, cy+dy-1, cx+dx+1, cy+dy+1), fill=ink)

sharingan(225, 106, 5)
sharingan(239, 137, 5)

# Make the forehead protector's spiral emblem readable at panel resolution.
draw.ellipse((250, 99, 271, 120), outline=ink, width=2)
draw.arc((255, 103, 267, 116), 195, 500, fill=ink, width=2)
draw.line([(264, 109), (267, 105)], fill=ink, width=2)
draw.line([(249, 99), (272, 121)], fill=red, width=2)

# Add a few bold crows and wind strokes in open background areas.
def crow(cx, cy, scale=1.0):
    points = [(-15, 0), (-8, -4), (-5, -11), (0, -6), (5, -11),
              (8, -3), (16, 0), (7, 2), (2, 8), (-2, 2)]
    draw.polygon([(cx + int(x*scale), cy + int(y*scale)) for x, y in points], fill=ink)

crow(86, 26, 0.8)
crow(151, 34, 0.65)
crow(380, 42, 0.75)
draw.arc((307, 40, 391, 128), 205, 320, fill=ink, width=2)
draw.arc((310, 45, 385, 122), 25, 135, fill=red, width=2)
draw.line([(287, 27), (300, 18), (314, 14)], fill=red, width=2)
draw.line([(372, 165), (387, 157), (398, 155)], fill=ink, width=2)

output = folder / "image_data_artwork.png"
image.save(output)
print(output)
