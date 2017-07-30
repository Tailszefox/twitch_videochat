import common

# Message sent by viewer
class ChatMessage():

    def __init__(self, fullObject):
        att = fullObject["attributes"]

        self.time = att["video-offset"]
        self.nick = att["tags"]["display-name"] if att["tags"]["display-name"] is not None else att["from"]
        self.color = self.adjustColor(att["tags"]["color"]) if att["tags"]["color"] is not None else self.generateColor()

        self.rawMessage = att["message"]
        self.message = self.wrapMessage()

        self.dimensions = self.getDimensions()

        self.timeToNext = 0
        self.currentY = 720

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
        # Try each wrapper until it fits
        for wrapper in common.wrappers:
            wrappedMessage = wrapper.fill(self.rawMessage)
            widthMessage, heightMessage = common.baseDraw.textsize(wrappedMessage, common.fonts["verdana"])

            if widthMessage <= 240:
                return wrappedMessage

        raise Exception("Could not wrap message...")

    # Get nick and message heights and widths
    def getDimensions(self):
        widthNick, heightNick = common.baseDraw.textsize(self.nick, common.fonts["verdanaBold"])
        widthMessage, heightMessage = common.baseDraw.textsize(self.message, common.fonts["verdana"])

        dimensions = {"nick": {}, "message": {}}
        dimensions["nick"] = {"width": widthNick, "height": heightNick}
        dimensions["message"] = {"width": widthMessage, "height": heightMessage}
        dimensions["total"] = {"height": common.spaceForNick + heightMessage}

        return dimensions

    def __str__(self):
        return "[{time}/{timeToNext}] {nick}({color}) [{nickWidth}x{nickHeight}]:\n[{messageWidth}x{messageHeight}]\n\"{message}\"".format(
            time = self.time, timeToNext = self.timeToNext, nick = self.nick, color = self.color,
            nickWidth = self.dimensions["nick"]["width"], nickHeight = self.dimensions["nick"]["height"],
            messageWidth = self.dimensions["message"]["width"], messageHeight = self.dimensions["message"]["height"],
            message = self.message)
