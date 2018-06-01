#!/usr/bin/env python3

import argparse
import sys
import re
import os
import subprocess

import make_frames
from youtube_dl import youtube_dl

parser = argparse.ArgumentParser()
parser.add_argument("--no-scrolling", action = "store_true", help = "disable scrolling")
parser.add_argument("videoUrl", help = "URL to Twitch video, ie. https://www.twitch.tv/videos/123456789")

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

arguments = parser.parse_args()

videoUrl = arguments.videoUrl
scrolling = not arguments.no_scrolling

print("\033[1mTwitch Videochat, working on video {}\033[0m".format(videoUrl))

regexTwitchVod = re.compile(r"https?://(www\.)?twitch\.tv/videos/([0-9]+)$")
videoIdMatch = regexTwitchVod.findall(videoUrl)

if len(videoIdMatch) == 0:
    print("{} is not a valid URL".format(videoUrl))
    sys.exit(1)

videoId = videoIdMatch[0][1]

os.makedirs("output/{}".format(videoId), exist_ok = True)
os.chdir("output/{}".format(videoId))

print("\n\033[1mDownloading chat...\033[0m")

if os.path.exists("./rechat-{}.json".format(videoId)):
    print("Chat already downloaded, skipping...")
else:
    subprocess.call(["python", "../../rechat-dl/rechat-dl.py", videoId])

if not os.path.exists("./rechat-{}.json".format(videoId)):
    print("Chat failed to download. Please check rechat-dl output.")
    sys.exit(1)

print("\n\033[1mDownloading video...\033[0m")

if os.path.exists("./v{}.mp4".format(videoId)):
    print("Video already downloaded, skipping...")
else:
    ydlOptions = {'format': 'best[height<=720][ext=mp4]',
                  'outtmpl': "%(id)s.%(ext)s",
                  'restrictfilenames': True
                 }

    try:
        with youtube_dl.YoutubeDL(ydlOptions) as ydl:
            ydl.download([videoUrl])
    except:
        print("Video failed to download in 720p, trying default format...")
        ydlOptions["format"] = "best[ext=mp4]"

        try:
            with youtube_dl.YoutubeDL(ydlOptions) as ydl:
                ydl.download([videoUrl])
        except:
            print("Video failed to download. Please check youtube-dl output.")
            sys.exit(1)

print("\n\033[1mGenerating frames...\033[0m")

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

print("\n\033[1mRendering video...\033[0m")

try:
    ffmpegCall = ["ffmpeg", "-threads", "4", "-i", "./v{}.mp4".format(videoId), "-safe", "0", "-i", "{}".format(concatFilename), "-filter_complex", "[0:v]scale=width=1030:height=580[scaled];[scaled]pad=w=1280:height=720:y=70[padded];[padded][1:v]overlay=x=1030:y=0[video]", "-map", "[video]", "-map", "0:1", "-acodec", "copy", "-preset", "ultrafast", "{}".format(outputFilename)]
    subprocess.call(ffmpegCall)
except:
    print("Video generation failed. Please check ffmpeg output.")
    sys.exit(1)

if not os.path.exists("./{}".format(outputFilename)):
    print("Video generation failed. Please check ffmpeg output.")
    sys.exit(1)

print("\n\033[1mDone! The rendered video is available at the following location: \033[0m./output/{}/{}".format(videoId, outputFilename))
