import textwrap
from PIL import Image, ImageDraw, ImageFont

# Create a new image
def getNewBaseImage():
    im = Image.new("RGBA", (250, 720), "black")
    draw = ImageDraw.Draw(im)

    return (im, draw)

# Draw borders around image
def drawBorders(draw):
    ## Up
    draw.rectangle([0, 0, 250, 4], "gray", "gray")
    ## Down
    draw.rectangle([0, 720, 250, 716], "gray", "gray")
    ## Left
    draw.rectangle([0, 0, 4, 720], "gray", "gray")
    ## Right
    draw.rectangle([250, 0, 246, 720], "gray", "gray")

# Write frame to disk
def writeFrame(frame):
    # Get new image
    im, draw = getNewBaseImage()

    for m in frame.messages:
        message = m["message"]
        position = m["position"]

        draw.text((8, position), "{}:".format(message.nick), message.color, fonts["verdanaBold"])
        draw.text((8, position + spaceForNick), message.message, "white", fonts["verdana"])

    drawBorders(draw)
    im.save("./{}/{}.png".format(framesDirectory, frame.name), "PNG")

# Convert miliseconds to HH:MM:SS:QQQ
def convertMs(ms):
    t = ms // 1000
    seconds = t % 60
    remainingMs = ms - (t * 1000)

    t = t // 60
    minutes = t % 60

    t = t // 60
    hours = t % 24

    return "{:0>2}:{:0>2}:{:0>2}.{:0>3}".format(hours, minutes, seconds, remainingMs)

# Scrolling can be enabled/disabled
scrolling = None

# Directory where frames are stored
framesDirectory = None

# Fonts used
fonts = {
    "verdana": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf", 17),
    "verdanaBold": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf", 17)
    }

# Bunch of wrappers to make messages fit on screen
wrappers = []
for width in range(25, 10, -1):
    wrappers.append(textwrap.TextWrapper(width = width))

# Space reserved for nick in pixels
spaceForNick = 20

# Scroll speed in pixels (how much to scroll up)
scrollSpeed = 5

# Time to display each scroll frame in ms
normalScrollDisplayTime = 32

# Base image used for size calculations
baseImage, baseDraw = getNewBaseImage()
