import os
import common

# Animation frame for chat overlay
class ChatFrame():
    def __init__(self, messageNo, scrollNo, messages, positions):
        self.messageNo = messageNo
        self.scrollNo = scrollNo
        self.name = "{}_{}".format(messageNo, scrollNo)

        self.rendered = False

        # Was the frame already rendered during a previous run?
        if os.path.exists("./{}/{}.png".format(common.framesDirectory, self.name)):
            self.rendered = True

        self.messages = []

        for i in range(0, len(messages)):
            message = messages[i]
            position = positions[i]

            self.messages.append({"message": message, "position": position})

    def __str__(self):
        r = ""

        for m in self.messages:
            r += "-> Message [{message}] at [{position}]\n".format(message = m["message"].rawMessage, position = m["position"])

        return "[Frame name {name}][{nbMessages} message{s}]\n{messages}".format(
            name = self.name, nbMessages = len(self.messages), messages = r, s = "s" if len(self.messages) > 1 else "")
