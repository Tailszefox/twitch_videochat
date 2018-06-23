#!/usr/bin/env python3

import argparse
import sys
import json
import re
import os
import subprocess
import textwrap
import shutil
import platform
import multiprocessing

from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from youtube_dl import youtube_dl

from ChatMessage import ChatMessage
from ChatFrame import ChatFrame

# Print the requested message in bold on supported OSes
def printBold(message):
    if platform.system() == "Windows":
        print(message)
    else:
        print("\033[1m{}\033[0m".format(message))

# Render the ChatFrame passed using its renderFrame method
def renderRequestedFrame(frameAndArguments):
    frame = frameAndArguments["frame"]

    frame.renderFrame(
        frameAndArguments["chatWidth"],
        frameAndArguments["videoHeight"],
        frameAndArguments["fontSize"],
        frameAndArguments["framesDirectory"]
    )

def main():
    # Check that ffmpeg and ffprobe exist
    ffmpegExe = shutil.which("ffmpeg")
    ffprobeExe = shutil.which("ffprobe")

    if ffmpegExe is None or ffprobeExe is None:
        print("You are missing ffmpeg and/or ffprobe. Please consult the README to know where to get them.")
        sys.exit(1)

    # On Windows, we want the full path to the executables
    if platform.system() == "Windows":
        ffmpegExe = os.path.dirname(os.path.realpath(__file__)) + "\\ffmpeg.exe"
        ffprobeExe = os.path.dirname(os.path.realpath(__file__)) + "\\ffprobe.exe"

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-scrolling", action = "store_true", help = "disable scrolling")
    parser.add_argument("videoUrl", help = "URL to Twitch video, ie. https://www.twitch.tv/videos/123456789")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    arguments = parser.parse_args()

    videoUrl = arguments.videoUrl
    scrolling = not arguments.no_scrolling

    printBold("Twitch Videochat, working on video {}".format(videoUrl))

    regexTwitchVod = re.compile(r"https?://(www\.)?twitch\.tv/videos/([0-9]+)$")
    videoIdMatch = regexTwitchVod.findall(videoUrl)

    if len(videoIdMatch) == 0:
        print("{} is not a valid URL".format(videoUrl))
        sys.exit(1)

    videoId = videoIdMatch[0][1]

    os.makedirs("output/{}".format(videoId), exist_ok = True)
    os.chdir("output/{}".format(videoId))

    printBold("\nDownloading chat...")

    chatFilename = "rechat-{}.json".format(videoId)

    if os.path.exists("./{}".format(chatFilename)):
        print("Chat already downloaded, skipping...")
    else:
        subprocess.call(["python", "../../rechat-dl/rechat-dl.py", videoId])

    if not os.path.exists("./{}".format(chatFilename)):
        print("Chat failed to download. Please check rechat-dl output.")
        sys.exit(1)

    printBold("\nDownloading video...")

    if os.path.exists("./v{}.mp4".format(videoId)):
        print("Video already downloaded, skipping...")
    else:
        ydlOptions = {'format': 'best[ext=mp4]',
                      'outtmpl': "%(id)s.%(ext)s",
                      'restrictfilenames': True,
                      'ffmpeg_location': ffmpegExe
                     }

        try:
            with youtube_dl.YoutubeDL(ydlOptions) as ydl:
                ydl.download([videoUrl])
        except:
            print("Video failed to download. Please check youtube-dl output.")
            sys.exit(1)

    printBold("\nParsing video size...")

    try:
        videoSize = subprocess.check_output([ffprobeExe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height,width", "-of", "csv=s=x:p=0", "./v{}.mp4".format(videoId)]).decode("utf-8")

        videoWidth = int(videoSize.split('x')[0])
        videoHeight = int(videoSize.split('x')[1])

        # The chat takes 20% of the video's original width
        paddedWidth = int((80 * videoWidth) / 100)
        chatWidth = videoWidth - paddedWidth

        # Pick font size according to resolution
        fontSize = int(videoHeight * 0.024)
        if fontSize < 8:
            fontSize = 8

        fonts = {
            "verdana": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf", fontSize),
            "verdanaBold": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf", fontSize)
        }
    except Exception as e:
        raise Exception("Could not extract video dimensions. Please check ffprobe output.") from e

    print("Video size: {videoWidth}x{videoHeight}\nChat size: {chatWidth}x{videoHeight}\nFont size: {fontSize}".format(videoWidth = videoWidth, videoHeight = videoHeight, chatWidth = chatWidth, fontSize = fontSize))

    printBold("\nGenerating frames...")

    # Create base image for size calculations
    baseImage = Image.new("RGBA", (chatWidth, videoHeight), "black")
    baseDraw = ImageDraw.Draw(baseImage)

    if scrolling:
        concatFilename = "rechat-{}.concat".format(videoId)
        framesDirectory = "frames"
        outputFilename = "{}_chat.mp4".format(videoId)
    else:
        concatFilename = "rechat-noscroll-{}.concat".format(videoId)
        framesDirectory = "frames_noscroll"
        outputFilename = "{}_chat_noscroll.mp4".format(videoId)

    os.makedirs("{}".format(framesDirectory), exist_ok = True)

    # Start generating frames
    # Scroll speed in pixels - ie. how much to scroll up on each frame
    scrollSpeed = 5

    # Time to display each scroll frame in ms
    normalScrollDisplayTime = 32

    print("Parsing chat log from {}...".format(chatFilename))
    with open(chatFilename) as j:
        chat = json.load(j)

        # First element is video info
        video = chat[0]
        chat = chat[1:]

    messages = []
    lastMessage = None
    messageNo = 0

    # Create ChatMessage object for each message
    for m in tqdm(chat, unit = "messages"):
        messageNo += 1

        newMessage = ChatMessage(m, baseDraw, fonts, chatWidth, videoHeight)
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

    with open(concatFilename, mode = "w") as f:
        # Make first blank image
        firstFrame = ChatFrame(0, 0, [], [], framesDirectory)
        firstFrame.renderFrame(chatWidth, videoHeight, fontSize, framesDirectory)

        print("ffconcat version 1.0", file = f)
        print("file ./{}/0_0.png".format(framesDirectory), file = f)
        print("duration {}".format(convertMs(messages[0].time)), file = f)

        timeForScrolling = 0

        print("\nCalculating necessary number of frames...")

        for m in tqdm(messages, unit = "messages"):
            messageNo += 1
            scrollNo = 0

            messageQueue.append(m)

            # Scroll until the last message is in frame
            while m.currentY + m.dimensions["total"]["height"] > (videoHeight - 10):
                frameMessages = []
                framePositions = []

                for mq in messageQueue:
                    mq.currentY -= scrollSpeed

                    frameMessages.append(mq)
                    framePositions.append(mq.currentY)

                # Add the frame to be rendered if we want scrolling
                if scrolling:
                    newFrame = ChatFrame(messageNo, scrollNo, frameMessages, framePositions, framesDirectory)
                    frameList.append(newFrame)

                scrollNo += 1

            # If we don't want scrolling, we only need to render the final frame for the message
            if not scrolling:
                lastFrame = ChatFrame(messageNo, 0, frameMessages, framePositions, framesDirectory)
                frameList.append(lastFrame)

                print("file ./{}/{}_0.png".format(framesDirectory, messageNo), file = f)
                print("duration {}".format(convertMs(m.timeToNext)), file = f)
            else:
                for frame in range(0, scrollNo):
                    print("file ./{}/{}_{}.png".format(framesDirectory, messageNo, frame), file = f)

                    if frame <= 1:
                        scrollDisplayTime = normalScrollDisplayTime * 2
                    elif frame >= (scrollNo - 2):
                        scrollDisplayTime = normalScrollDisplayTime * 2
                    else:
                        scrollDisplayTime = normalScrollDisplayTime

                    print("duration {}".format(convertMs(scrollDisplayTime)), file = f)

                    timeForScrolling += scrollDisplayTime

                timeToNextWithScrolling = m.timeToNext - timeForScrolling

                # If we have to wait until the next message, display the last image until it's time for the next one
                if timeToNextWithScrolling > 0:
                    print("file ./{}/{}_{}.png".format(framesDirectory, messageNo, scrollNo - 1), file = f)
                    print("duration {}".format(convertMs(timeToNextWithScrolling)), file = f)
                    timeForScrolling = 0
                # We took too much time to scroll, so we'll need to display the next message for less time
                else:
                    timeForScrolling = -timeToNextWithScrolling

            # Remove messages from the queue if they scrolled offscreen
            messageQueue = [mq for mq in messageQueue if mq.currentY + mq.dimensions["total"]["height"] > 0]

    print("\nGenerating {} frames for {} messages{}...".format(len(frameList), len(messages), "" if scrolling else " with no scrolling"))

    # Force non-Windows OSes to use the spawn method, to behave the same as Windows
    if platform.system() != "Windows":
        multiprocessing.set_start_method('spawn')

    pool = multiprocessing.Pool()

    # Store some necessary arguments alongside each frame to be able to render it
    framesAndArguments = []
    for f in frameList:
        d = {}
        d["frame"] = f
        d["chatWidth"] = chatWidth
        d["videoHeight"] = videoHeight
        d["fontSize"] = fontSize
        d["framesDirectory"] = framesDirectory

        framesAndArguments.append(d)

    list(tqdm(pool.imap(renderRequestedFrame, framesAndArguments), total = len(frameList), unit = "frames"))

    pool.close()
    pool.join()

    if not os.path.exists("./{}".format(concatFilename)):
        print("Frame generation failed. Please check console ouptut.")
        sys.exit(1)

    printBold("\nRendering video...")

    try:
        ffmpegCall = [ffmpegExe, "-threads", "4", "-i", "./v{}.mp4".format(videoId), "-safe", "0", "-i", "{}".format(concatFilename), "-filter_complex",
        "[0:v]scale=width={paddedWidth}:height=-1[scaled];[scaled]pad=w={videoWidth}:height={videoHeight}:y=(oh-ih)/2[padded];[padded][1:v]overlay=x={paddedWidth}:y=0[video]".format(paddedWidth = paddedWidth, videoWidth = videoWidth, videoHeight = videoHeight),
        "-map", "[video]", "-map", "0:1", "-acodec", "copy", "-preset", "ultrafast", "{}".format(outputFilename)]

        subprocess.call(ffmpegCall)
    except:
        print("Video generation failed. Please check ffmpeg output.")
        sys.exit(1)

    if not os.path.exists("./{}".format(outputFilename)):
        print("Video generation failed. Please check ffmpeg output.")
        sys.exit(1)

    printBold("\nDone! The rendered video is available at the following location: ")
    print("./output/{}/{}".format(videoId, outputFilename))

if __name__ == '__main__':
    main()
