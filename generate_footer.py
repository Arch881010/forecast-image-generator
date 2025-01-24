from PIL import Image, ImageDraw, ImageFont
from config import *
import os

def generate_footer(last_update_time, generated_time):
    # Open the image to get its width
    img = Image.open(file)
    width, _ = img.size

    width = int(width * width_multiplier)

    # Create a new image for the footer
    footer_height = header_height
    footer_image = Image.new('RGB', (width, footer_height), footer_color)

    # Initialize ImageDraw
    draw = ImageDraw.Draw(footer_image)

    # Define the text and font
    text = f"Current Conditions as of {last_update_time} | Generated: {generated_time}"
    font_path = os.path.join(os.path.dirname(__file__), 'arial.ttf')
    #font = ImageFont.truetype(font_path, 15)

   # Calculate text width and height to center it
    text_bbox = draw.textbbox((0, 0), text, font=footer_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (footer_height - text_height) // 2

    # Add the text to the image
    draw.text((text_x, text_y), text, fill="white", font=footer_font)

    # Save the footer image
    footer_image.save('output/footer.png')
