import textwrap
from PIL import Image, ImageDraw, ImageFont

# Create a new image
def getNewBaseImage():
    im = Image.new("RGBA", (chatWidth, videoHeight), "black")
    draw = ImageDraw.Draw(im)

    return (im, draw)

# Draw borders around image
def drawBorders(draw):
    ## Up
    draw.rectangle([0, 0, chatWidth, 5], "gray", "gray")
    ## Down
    draw.rectangle([0, videoHeight, chatWidth, videoHeight - 5], "gray", "gray")
    ## Left
    draw.rectangle([0, 0, 5, videoHeight], "gray", "gray")
    ## Right
    draw.rectangle([chatWidth, 0, chatWidth - 5, videoHeight], "gray", "gray")

# Write frame to disk
def writeFrame(frame):
    # Skip the frame if it's already been rendered
    if frame.rendered:
        return

    # Get new image
    im, draw = getNewBaseImage()

    for m in frame.messages:
        message = m["message"]
        position = m["position"]

        draw.text((10, position), "{}:".format(message.nick), message.color, fonts["verdanaBold"])
        draw.text((10, position + message.dimensions["nick"]["height"]), message.message, "white", fonts["verdana"])

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

# Video and chat size
videoWidth = 0
videoHeight = 0
paddedWidth = 0
chatWidth = 0

# Scrolling can be enabled/disabled
scrolling = None

# Directory where frames are stored
framesDirectory = None

# Fonts used
fonts = None

# Scroll speed in pixels (how much to scroll up)
scrollSpeed = 5

# Time to display each scroll frame in ms
normalScrollDisplayTime = 32

# Base image used for size calculations
baseImage = None
baseDraw = None
