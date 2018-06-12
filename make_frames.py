#!/usr/bin/env python3

import sys
import json
import argparse
import textwrap
import platform
from tqdm import tqdm
from multiprocessing import Pool

import common
from ChatMessage import ChatMessage
from ChatFrame import ChatFrame

def main(videoId, scrolling):
    clipId = videoId
    common.scrolling = scrolling

    filename = "rechat-{}.json".format(clipId)

    if common.scrolling:
        filenameConcat = "rechat-{}.concat".format(clipId)
        common.framesDirectory = "frames"
    else:
        filenameConcat = "rechat-noscroll-{}.concat".format(clipId)
        common.framesDirectory = "frames_noscroll"

    try:
        print("Parsing chat log from {}...".format(filename))
        with open(filename) as j:
            chat = json.load(j)

            # First element is video info
            video = chat[0]
            chat = chat[1:]
    except FileNotFoundError:
        print("Can't find chat file {}".format(filename))
        sys.exit(1)

    messages = []
    lastMessage = None
    messageNo = 0

    # Create ChatMessage object for each message
    for m in tqdm(chat, unit = "messages"):
        messageNo += 1

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

    with open(filenameConcat, mode = "w") as f:
        # Make first blank image
        im, draw = common.getNewBaseImage()
        common.drawBorders(draw)
        im.save("./{}/0_0.png".format(common.framesDirectory), "PNG")

        print("ffconcat version 1.0", file = f)
        print("file ./{}/0_0.png".format(common.framesDirectory), file = f)
        print("duration {}".format(common.convertMs(messages[0].time)), file = f)

        timeForScrolling = 0

        print("\nCalculating necessary number of frames...")

        for m in tqdm(messages, unit = "messages"):
            messageNo += 1
            scrollNo = 0

            messageQueue.append(m)

            # Scroll until the last message is in frame
            while m.currentY + m.dimensions["total"]["height"] > (common.videoHeight - 10):
                frameMessages = []
                framePositions = []

                for mq in messageQueue:
                    mq.currentY -= common.scrollSpeed

                    frameMessages.append(mq)
                    framePositions.append(mq.currentY)

                # Add the frame to be rendered if we want scrolling
                if common.scrolling:
                    newFrame = ChatFrame(messageNo, scrollNo, frameMessages, framePositions)
                    frameList.append(newFrame)

                scrollNo += 1

            # If we don't want scrolling, we only need to render the final frame for the message
            if not common.scrolling:
                lastFrame = ChatFrame(messageNo, 0, frameMessages, framePositions)
                frameList.append(lastFrame)

                print("file ./{}/{}_0.png".format(common.framesDirectory, messageNo), file = f)
                print("duration {}".format(common.convertMs(m.timeToNext)), file = f)
            else:
                for frame in range(0, scrollNo):
                    print("file ./{}/{}_{}.png".format(common.framesDirectory, messageNo, frame), file = f)

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
                    print("file ./{}/{}_{}.png".format(common.framesDirectory, messageNo, scrollNo - 1), file = f)
                    print("duration {}".format(common.convertMs(timeToNextWithScrolling)), file = f)
                    timeForScrolling = 0
                # We took too much time to scroll, so we'll need to display the next message for less time
                else:
                    timeForScrolling = -timeToNextWithScrolling

            # Remove messages from the queue if they scrolled offscreen
            messageQueue = [mq for mq in messageQueue if mq.currentY + mq.dimensions["total"]["height"] > 0]

    print("\nGenerating {} frames for {} messages{}...".format(len(frameList), len(messages), "" if common.scrolling else " with no scrolling"))

    # TODO add multithreading support for Windows
    if platform.system() == "Windows":
        for f in tqdm(frameList, unit = "frames"):
            common.writeFrame(f)
    else:
        pool = Pool()
        list(tqdm(pool.imap(common.writeFrame, frameList), total = len(frameList), unit = "frames"))
        pool.close()
        pool.join()

if __name__=='__main__':
    print("This script should not be called on its own. Call twitch_videochat.py instead.")
