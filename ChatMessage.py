import common
import textwrap

# Message sent by viewer
class ChatMessage():

    def __init__(self, obj):
        self.time = int(obj["content_offset_seconds"] * 1000)
        self.nick = obj["commenter"]["display_name"] if obj["commenter"]["display_name"] is not None else obj["commenter"]["name"]

        try:
            self.color = self.adjustColor(obj["message"]["user_color"])
        except KeyError:
            self.color = self.generateColor()

        self.rawMessage = obj["message"]["body"]
        self.message = self.wrapMessage()

        self.dimensions = self.getDimensions()

        self.timeToNext = 0

        # All messages start below the bottom of the video
        self.currentY = common.videoHeight

    # Adjust nick color so it's not too dark
    def adjustColor(self, color):
        # Grab each color value
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        # Return directly if it's bright enough
        if r > 20 or g > 20 or b > 20:
            return color

        # Otherwise, just set the red channel to 20 to make sure it's visible
        return "#{:0>2X}{:0>2X}{:0>2X}".format(20, g, b)

    # Generate color based on nick
    def generateColor(self):
        r, g, b = 0, 0, 0
        for letter in self.nick:
            r = ord(letter) % 255
            g = ord(letter) * 100 % 255
            b = ord(letter) * 200 % 255

        color = self.adjustColor("#{:0>2X}{:0>2X}{:0>2X}".format(r, g, b))
        return color

    # Wrap message so it fits on screen
    def wrapMessage(self):
        maximumTextLength = 0
        wrappedMessage = None
        previousWrappedMessage = None

        # Try to have as many characters as possible on a line until it exceeds the chat's length
        while True:
            maximumTextLength += 5

            previousWrappedMessage = wrappedMessage
            wrappedMessage = textwrap.fill(self.rawMessage, width = maximumTextLength)
            widthMessage, heightMessage = common.baseDraw.textsize(wrappedMessage, common.fonts["verdana"])

            # We exceeded the allowed length
            if widthMessage >= (common.chatWidth - 20):
                return previousWrappedMessage

            # We already have everythign on a single line
            if "\n" not in wrappedMessage:
                return wrappedMessage

    # Get nick and message heights and widths
    def getDimensions(self):
        widthNick, heightNick = common.baseDraw.textsize(self.nick, common.fonts["verdanaBold"])
        widthMessage, heightMessage = common.baseDraw.textsize(self.message, common.fonts["verdana"])

        dimensions = {"nick": {}, "message": {}}
        dimensions["nick"] = {"width": widthNick, "height": heightNick}
        dimensions["message"] = {"width": widthMessage, "height": heightMessage}
        dimensions["total"] = {"height": heightNick + heightMessage}

        return dimensions

    def __str__(self):
        return "[{time}/{timeToNext}] {nick}({color}) [{nickWidth}x{nickHeight}]:\n[{messageWidth}x{messageHeight}]\n\"{message}\"".format(
            time = self.time, timeToNext = self.timeToNext, nick = self.nick, color = self.color,
            nickWidth = self.dimensions["nick"]["width"], nickHeight = self.dimensions["nick"]["height"],
            messageWidth = self.dimensions["message"]["width"], messageHeight = self.dimensions["message"]["height"],
            message = self.message)
