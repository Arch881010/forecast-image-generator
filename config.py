from PIL import ImageFont
# Current colors
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
# Add other colors here


# config that are changeable

# Sizes
header_height    = 40
font_size        = 20
spacing          = 15

# Font sizes (optional)
header_font_size = 20
footer_font_size = 15


# Location Text
location_title   = "Example Location"

# City and its latitude and longitiude 
# You will have to get it's lat and lon manually, for now
# Also its up to 4 decimal places
city             = "Washington, D.C."
lat              = "38.9072"
lon              = "-77.0369"

# Default image title
image_title      = "Today's Forecast"

# Observation station
# This can be found at https://www.weather.gov/
# Get the city that you want, and the 4 letter code
# That says Current observations at (code)
wx_obs_station   = "KDCA" 

# Background image
folder           = "transparent_icons"
fileName         = "example.png"

# Default text color and background color
text_color       = white
background_color = black

# Header text and color
header_color     = black
footer_color     = black

# Header text... ez
header_text      = "Header"

# font
default_font     = 'Gotham-Black.otf'
header_font      = ''
footer_font      = 'Arial.ttf'

# timezone
timezone         = "America/Chicago"

# debug
debug            = False

# is production?
isProduction     = False

# Image Stuff
# Center_Image can change or not, doesn't matter.
# Width Multiplier 
center_image     = True
width_multiplier = 1
max_width        = 1300

# DO NOT CHANGE
file = f'{folder}/{fileName}'

font = ImageFont.truetype(("fonts/" + default_font), font_size)

if header_font_size == 0:
    header_font_size = font_size

if footer_font_size == 0:
    footer_font_size = font_size

if header_font == '':
    header_font = ImageFont.truetype(("fonts/" + default_font), header_font_size)
else:
    header_font = ImageFont.truetype(("fonts/" + header_font), header_font_size)

if footer_font == '':
    footer_font = ImageFont.truetype(("fonts/" + default_font), footer_font_size)
else:
    footer_font = ImageFont.truetype(("fonts/" + footer_font), footer_font_size)

loop = True

