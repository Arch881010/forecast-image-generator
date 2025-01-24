from PIL import Image, ImageDraw, ImageFont
from config import *
import os


def generate_header(header_text):

    # Open the weather forecast image to get its width
    weather_image = Image.open(file)
    width, _ = weather_image.size

    width = int(width * width_multiplier)

    # Create a new image with the same width, height of 20px, and black background

    header_image = Image.new('RGB', (width, header_height), header_color)

    # Initialize ImageDraw
    draw = ImageDraw.Draw(header_image)

    # font
    font_path = os.path.join(os.path.dirname(__file__), 'arial.ttf')
    #font = ImageFont.truetype(font_path, 20)

    # Calculate text width and height to center it
    text_bbox = draw.textbbox((0, 0), header_text, font=header_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (header_height - text_height) // 2

    # Add the text to the image
    draw.text((text_x, text_y), header_text, fill=text_color, font=header_font)

    # Save the header image
    header_image.save('output/header.png')