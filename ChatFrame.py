import os
from PIL import Image, ImageDraw, ImageFont

# Animation frame for chat overlay
class ChatFrame():
    def __init__(self, messageNo, scrollNo, messages, positions, framesDirectory):
        self.messageNo = messageNo
        self.scrollNo = scrollNo
        self.name = "{}_{}".format(messageNo, scrollNo)

        self.rendered = False

        # Was the frame already rendered during a previous run?
        if os.path.exists("./{}/{}.png".format(framesDirectory, self.name)):
            self.rendered = True

        self.messages = []

        for i in range(0, len(messages)):
            message = messages[i]
            position = positions[i]

            self.messages.append({"message": message, "position": position})

    # Draw borders around frame
    def drawBorders(self, draw, chatWidth, videoHeight):
        ## Up
        draw.rectangle([0, 0, chatWidth, 5], "gray", "gray")
        ## Down
        draw.rectangle([0, videoHeight, chatWidth, videoHeight - 5], "gray", "gray")
        ## Left
        draw.rectangle([0, 0, 5, videoHeight], "gray", "gray")
        ## Right
        draw.rectangle([chatWidth, 0, chatWidth - 5, videoHeight], "gray", "gray")

    # Render frame and write it to disk
    def renderFrame(self, chatWidth, videoHeight, fontSize, framesDirectory):
        # Skip the frame if it's already been rendered
        if self.rendered:
            return

        # Make new image
        im = Image.new("RGBA", (chatWidth, videoHeight), "black")
        draw = ImageDraw.Draw(im)

        # We can't pickle Fonts objects, so we have to recreate them
        fonts = {
            "verdana": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf", fontSize),
            "verdanaBold": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf", fontSize)
        }

        for m in self.messages:
            message = m["message"]
            position = m["position"]

            draw.text((10, position), "{}:".format(message.nick), message.color, fonts["verdanaBold"])
            draw.text((10, position + message.dimensions["nick"]["height"]), message.message, "white", fonts["verdana"])

        self.drawBorders(draw, chatWidth, videoHeight)
        im.save("./{}/{}.png".format(framesDirectory, self.name), "PNG")

    def __str__(self):
        r = ""

        for m in self.messages:
            r += "-> Message [{message}] at [{position}]\n".format(message = m["message"].rawMessage, position = m["position"])

        return "[Frame name {name}][{nbMessages} message{s}]\n{messages}".format(
            name = self.name, nbMessages = len(self.messages), messages = r, s = "s" if len(self.messages) > 1 else "")
