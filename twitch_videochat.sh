#!/bin/bash

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 https://www.twitch.tv/videos/123456789"
    exit
fi

bold=$(tput bold)
normal=$(tput sgr0)

url="$1"
regexTwitchVod=".*/videos/([0-9]+)$"

if [[ $url == *twitch.tv* ]]; then
    if [[ $url =~ $regexTwitchVod ]]; then
        n=${#BASH_REMATCH[*]}
        id=${BASH_REMATCH[1]}
        echo "Twitch VOD ID found: $id"
    else
        echo "No video ID found."
        exit
    fi
else
    echo "This URL is not valid."
    exit
fi

mkdir -p "output"
cd "output"

mkdir -p "$id"
cd "$id"

echo -e "\n${bold}Downloading video...${normal}\n"

quality='best[height<=720][ext=mp4]'

if [[ -f ../../youtube-convert ]]; then
    ../../youtube-convert -i -f "$quality" "$url"
else
    youtube-convert -i -f "$quality" "$url"
fi

if ! ls *$id.mp4 > /dev/null 2>&1; then
    echo "Video failed to download."
    exit
fi

echo -e "\n${bold}Downloading chat...${normal}\n"

if ls rechat-${id}.json > /dev/null 2>&1; then
    echo -e "Chat already downloaded, skipping..."
else
    python ../../rechat-dl/rechat-dl.py "$id"
fi

if ! ls rechat-${id}.json > /dev/null 2>&1; then
    echo "Chat failed to download."
    exit
fi

echo -e "\n${bold}Generating frames...${normal}\n"

if ls rechat-${id}.concat > /dev/null 2>&1; then
    echo -e "Concat file and frames already generated, skipping..."
else
    mkdir -p "frames"
    python3 ../../make_frames.py "$id"
fi

if ! ls rechat-${id}.concat > /dev/null 2>&1; then
    echo "Frame generation failed."
    exit
fi

echo -e "\n${bold}Rendering video...${normal}\n"

ffmpeg -threads 4 -i ./*${id}.mp4 -safe 0 -i ./rechat-${id}.concat -filter_complex "[0:v]scale=width=1030:height=580[scaled];[scaled]pad=w=1280:height=720:y=70[padded];[padded][1:v]overlay=x=1030:y=0[video]" -map "[video]" -map 0:1 -acodec copy -preset ultrafast ${id}_chat.mp4

if ! ls ${id}_chat.mp4 > /dev/null 2>&1; then
    echo -e "\nVideo rendering failed.\n"
    exit
fi

echo -e "\n${bold}Done!${normal}\n"
