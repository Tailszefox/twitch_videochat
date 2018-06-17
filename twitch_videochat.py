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
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm
from multiprocessing import Pool

import common
import make_frames
from youtube_dl import youtube_dl

# Print the requested message in bold on supported OSes
def printBold(message):
    if platform.system() == "Windows":
        print(message)
    else:
        print("\033[1m{}\033[0m".format(message))

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

    if os.path.exists("./rechat-{}.json".format(videoId)):
        print("Chat already downloaded, skipping...")
    else:
        subprocess.call(["python", "../../rechat-dl/rechat-dl.py", videoId])

    if not os.path.exists("./rechat-{}.json".format(videoId)):
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

        common.videoWidth = int(videoSize.split('x')[0])
        common.videoHeight = int(videoSize.split('x')[1])

        # The chat takes 20% of the video's original width
        common.paddedWidth = int((80 * common.videoWidth) / 100)
        common.chatWidth = common.videoWidth - common.paddedWidth

        # Pick font size according to resolution
        fontSize = int(common.videoHeight * 0.024)
        if fontSize < 8:
            fontSize = 8

        common.fonts = {
            "verdana": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdana.ttf", fontSize),
            "verdanaBold": ImageFont.truetype("/usr/share/fonts/truetype/msttcorefonts/verdanab.ttf", fontSize)
        }
    except Exception as e:
        raise Exception("Could not extract video dimensions. Please check ffprobe output.") from e

    print("Video size: {videoWidth}x{videoHeight}\nChat size: {chatWidth}x{videoHeight}\nFont size: {fontSize}".format(videoWidth = common.videoWidth, videoHeight = common.videoHeight, chatWidth = common.chatWidth, fontSize = fontSize))

    printBold("\nGenerating frames...")

    # Create base image for size calculations
    common.baseImage, common.baseDraw = common.getNewBaseImage()

    if scrolling:
        concatFilename = "rechat-{}.concat".format(videoId)
        framesDirectory = "frames"
        outputFilename = "{}_chat.mp4".format(videoId)
    else:
        concatFilename = "rechat-noscroll-{}.concat".format(videoId)
        framesDirectory = "frames_noscroll"
        outputFilename = "{}_chat_noscroll.mp4".format(videoId)

    os.makedirs("{}".format(framesDirectory), exist_ok = True)

    make_frames.main(videoId, scrolling)

    if not os.path.exists("./{}".format(concatFilename)):
        print("Frame generation failed. Please check make_frames.py output.")
        sys.exit(1)

    printBold("\nRendering video...")

    try:
        ffmpegCall = [ffmpegExe, "-threads", "4", "-i", "./v{}.mp4".format(videoId), "-safe", "0", "-i", "{}".format(concatFilename), "-filter_complex",
        "[0:v]scale=width={paddedWidth}:height=-1[scaled];[scaled]pad=w={videoWidth}:height={videoHeight}:y=(oh-ih)/2[padded];[padded][1:v]overlay=x={paddedWidth}:y=0[video]".format(paddedWidth = common.paddedWidth, videoWidth = common.videoWidth, videoHeight = common.videoHeight),
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
