#!/usr/bin/env python3

import sys
import json
from tqdm import tqdm
from multiprocessing import Pool

import common
from ChatMessage import ChatMessage
from ChatFrame import ChatFrame

try:
    clipId = sys.argv[1]
    filename = "rechat-{}.json".format(clipId)
    filenameConcat = "rechat-{}.concat".format(clipId)
except IndexError:
    print("Usage: {} [clip ID]".format(sys.argv[0]))
    sys.exit()

try:
    print("Reading chat log from {}...".format(filename))
    with open(filename) as j:
        chat = json.load(j)

        # First element is video info
        video = chat[0]
        chat = chat[1:]
except FileNotFoundError:
    print("Can't find chat file {}".format(filename))
    sys.exit()

messages = []
lastMessage = None
messageNo = 0

# Create ChatMessage object for each message
for m in tqdm(chat, unit = "messages"):
    messageNo += 1

    # Ignore room commands
    if m["attributes"]["command"] == "ROOMSTATE":
        continue

    newMessage = ChatMessage(m)
    messages.append(newMessage)

    try:
        lastMessage.timeToNext = newMessage.time - lastMessage.time
    except AttributeError:
        # lastMessage is None
        pass

    lastMessage = newMessage

# The very last message doesn't have a time to next, since there's no next message
lastMessage.timeToNext = 0

messageNo = 0
messageQueue = []
frameList = []

try:
    with open(filenameConcat, mode = "x") as f:
        # Make first blank image
        im, draw = common.getNewBaseImage()
        common.drawBorders(draw)
        im.save("./frames/0_0.png", "PNG")

        print("ffconcat version 1.0", file = f)
        print("file ./frames/0_0.png", file = f)
        print("duration {}".format(common.convertMs(messages[0].time)), file = f)

        timeForScrolling = 0

        print("\nCalculating necessary number of frames...")

        for m in tqdm(messages, unit = "messages"):
            messageNo += 1
            scrollNo = 0

            messageQueue.append(m)

            # Scroll until the last message is in frame
            while m.currentY + m.dimensions["total"]["height"] > 716:
                frameMessages = []
                framePositions = []

                for mq in messageQueue:
                    mq.currentY -= common.scrollSpeed

                    frameMessages.append(mq)
                    framePositions.append(mq.currentY)

                newFrame = ChatFrame(messageNo, scrollNo, frameMessages, framePositions)
                frameList.append(newFrame)

                scrollNo += 1

            for frame in range(0, scrollNo):
                print("file ./frames/{}_{}.png".format(messageNo, frame), file = f)

                if frame <= 1:
                    scrollDisplayTime = common.normalScrollDisplayTime * 2
                elif frame >= (scrollNo - 2):
                    scrollDisplayTime = common.normalScrollDisplayTime * 2
                else:
                    scrollDisplayTime = common.normalScrollDisplayTime

                print("duration {}".format(common.convertMs(scrollDisplayTime)), file = f)

                timeForScrolling += scrollDisplayTime

            timeToNextWithScrolling = m.timeToNext - timeForScrolling

            # If we have to wait until the next message, display the last image until it's time for the next one
            if timeToNextWithScrolling > 0:
                print("file ./frames/{}_{}.png".format(messageNo, scrollNo - 1), file = f)
                print("duration {}".format(common.convertMs(timeToNextWithScrolling)), file = f)
                timeForScrolling = 0
            # We took too much time to scroll, so we'll need to display the next message for less time
            else:
                timeForScrolling = -timeToNextWithScrolling

            # Remove messages from the queue if they scrolled offscreen
            messageQueue = [mq for mq in messageQueue if mq.currentY + mq.dimensions["total"]["height"] > 0]

except FileExistsError:
    print("Concat file already exists.")
    sys.exit()

print("\nGenerating {} frames for {} messages...".format(len(frameList), len(messages)))

pool = Pool()
list(tqdm(pool.imap(common.writeFrame, frameList), total = len(frameList), unit = "frames"))
pool.close()
pool.join()
