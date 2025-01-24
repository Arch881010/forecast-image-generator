def getTextSize(text):
    from PIL import Image, ImageDraw
    from config import header_height, font

    draw = ImageDraw.Draw(Image.new('RGB', (getWidth(), header_height)))
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    return (text_width, text_height)

def getWidth():
    from PIL import Image
    from config import file

    img = Image.open(file)
    return img.size[0]

def readStorage():
    from json import load

    try:
        with open('storage.json', 'r') as f:
            return load(f)
    except:
        return {}
    
def writeStorage(data):
    from json import dump

    saveData = {
        "high_temp": data["high_temp"],
    }

    with open('storage.json', 'w') as f:
        dump(data, f)