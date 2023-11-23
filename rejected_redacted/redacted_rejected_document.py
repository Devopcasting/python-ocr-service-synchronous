from PIL import Image, ImageDraw

class RedactRejectedDocument:
    def __init__(self, image_path) -> None:
        self.image_path = image_path
    
    def rejected(self):
        image = Image.open(self.image_path)
        # Get the dimensions of the image
        width, height = image.size
        # Create a new image with the same size and a white background
        redacted_image = Image.new("RGB", (width, height), "black")
        # Get a draw object to manipulate the new image
        draw = ImageDraw.Draw(redacted_image)
        # Redact 75% of the image horizontally
        redacted_width = int(height * 0.30)
        # Paste the unredacted part onto the new image
        redacted_image.paste(image.crop((0, 0, width, redacted_width)), (0, 0))
        redacted_image.save(self.image_path)