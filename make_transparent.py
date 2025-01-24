import sys
from PIL import Image

def make_image_transparent(filename, tolerance=200):
    try:
        img = Image.open(filename).convert("RGBA")
        datas = img.getdata()

        new_data = []
        for item in datas:
            # Change all white (also shades of whites) pixels to transparent
            if all(channel > tolerance for channel in item[:3]):
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)
        img.save("transparent_" + filename, "PNG")
        print(f"Image saved as transparent_{filename}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_transparent.py <filename>")
    else:
        filename = sys.argv[1]
        make_image_transparent(filename)