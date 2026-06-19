"""Generates the app icon (assets/icon.ico) programmatically -- a simple
speech-bubble mark, high-contrast, no external image assets needed."""

from PIL import Image, ImageDraw

SIZE = 256
BG = (30, 136, 229)  # blue
FG = (255, 255, 255)  # white

img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Circular background
margin = 8
draw.ellipse([margin, margin, SIZE - margin, SIZE - margin], fill=BG)

# Speech bubble (rounded rect + tail), representing "explain it to me"
bubble_box = [60, 70, 196, 160]
draw.rounded_rectangle(bubble_box, radius=24, fill=FG)
draw.polygon([(90, 158), (90, 196), (130, 158)], fill=FG)

# Three dots inside the bubble (a generic "speaking/translating" motif)
for cx in (98, 128, 158):
    draw.ellipse([cx - 9, 100, cx + 9, 118], fill=BG)

img.save("assets/icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (128, 128), (256, 256)])
img.save("assets/icon.png")
print("Saved assets/icon.ico and assets/icon.png")
