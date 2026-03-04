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

    with open('storage.json', 'w') as f:
        dump(data, f)

def updateKey(data, key, value):
    data[key] = value
    old_data = readStorage()
    old_data[key] = value
    writeStorage(old_data)

def addToStorage(data):
    old_data = readStorage()
    for key in data:
        old_data[key] = data[key]
    writeStorage(old_data)

def objectHasKey(data, key):
    return key in data


def correctText(str):
    if str == "Slight Chance Showers And Thunderstorms":
        str = "Slight Chance of Thunderstorms"
    if len(str) > 26:
        str = (str.split(" then"))[0] + " Early"

    return str 

# Function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(celsius):
    return round((celsius * 9 / 5) + 32)

def create_image(file=""):
    from PIL import Image, ImageDraw
    from config import background_color, width_multiplier, header_height, max_width, center_image

    if file == "":
        from config import file

    background = Image.open(file)

    if background.size[0] > max_width:
        raise Exception(
            "Image is too wide. Please use an image with a width of "
            + str(max_width)
            + "px or less.\n"
            + "Current width: "
            + str(background.size[0])
            + "px"
        )

    size = (
        int(background.size[0] * width_multiplier),
        background.size[1] + 2 * header_height,
    )

    img = Image.new("RGB", size, color=background_color)


    width = img.size[0]
    height = img.size[1]

    if center_image:
        img.paste(
            background, ((width - background.size[0]) // 2, header_height), background
        )
    else:
        img.paste(background, (0, header_height), background)

    return img

def create_backgroundless_image(dimensions):
    from PIL import Image
    from config import background_color

    return Image.new("RGB", dimensions, background_color)


def getCorrectedHeight(file=""):
    from config import header_height
    from PIL import Image

    if file == "":
        from config import file

    img = Image.open(file)
    return (img.size[1] + 2 * header_height - header_height)