"""Generates a synthetic official-notice image for testing the vision/OCR
pipeline without capturing a real screenshot."""

from PIL import Image, ImageDraw, ImageFont

TEXT = (
    "DEPARTMENT OF BENEFITS\n\n"
    "Your application for benefits has been received.\n"
    "To avoid a lapse in coverage, you must submit\n"
    "Form RRB-1099 and proof of income within 30 days\n"
    "of the date on this notice.\n\n"
    "Failure to respond may result in termination of benefits."
)

img = Image.new("RGB", (800, 400), color="white")
draw = ImageDraw.Draw(img)
font = ImageFont.load_default(size=20)
draw.multiline_text((40, 40), TEXT, fill="black", font=font, spacing=10)
img.save("samples/sample_notice.png")
print("Saved samples/sample_notice.png")
