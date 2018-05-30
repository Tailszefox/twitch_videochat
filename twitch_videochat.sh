#!/bin/bash

function usage()
{
    echo "Usage: $0 [--no-scrolling] https://www.twitch.tv/videos/123456789"
    exit
}

# Make option --no-scrolling available
options=$(getopt -o n --long no-scrolling -- "$@")

# Failed to parse options
if [[ $? -ne 0 ]]; then
    usage
fi

eval set -- "$options"

# Scrolling is enabled by default
scrolling=true

while true; do
    case "$1" in
        -n | --no-scrolling) scrolling=false; shift ;;
        --) shift ; break ;;
        *) break;;
    esac
done

# No URL provided
if [[ $# -eq 0 ]]; then
    usage
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

echo -e "\n${bold}Downloading video...${normal}\n"

quality='best[height<=720][ext=mp4]'
../../youtube_dl/youtube_dl/__main__.py -f "$quality" --restrict-filenames -o "%(upload_date)s - %(title)s - %(uploader)s - %(id)s.%(ext)s" "$url"

if ! ls *$id.mp4 > /dev/null 2>&1; then
    echo "Video failed to download in 720p, trying default format..."

    quality='best[ext=mp4]'
    ../../youtube_dl/youtube_dl/__main__.py -f "$quality" --restrict-filenames -o "%(upload_date)s - %(title)s - %(uploader)s - %(id)s.%(ext)s" "$url"

    if ! ls *$id.mp4 > /dev/null 2>&1; then
        echo "Video failed to download."
        exit
    fi
fi

echo -e "\n${bold}Generating frames...${normal}\n"

if $scrolling; then
    concatFilename="rechat-${id}.concat"
    framesDirectory="frames"
    outputFilename="${id}_chat.mp4"
    makeFramesOptions=""
else
    concatFilename="rechat-noscroll-${id}.concat"
    framesDirectory="frames_noscroll"
    outputFilename="${id}_chat_noscroll.mp4"
    makeFramesOptions="--no-scrolling"
fi

mkdir -p $framesDirectory
python3 ../../make_frames.py $makeFramesOptions "$id"

if [[ $? -ne 0 ]]; then
    echo "Python did not exit properly during frame generation."
    exit
fi

if ! ls $concatFilename > /dev/null 2>&1; then
    echo "Frame generation failed."
    exit
fi

echo -e "\n${bold}Rendering video...${normal}\n"

ffmpeg -threads 4 -i ./*${id}.mp4 -safe 0 -i $concatFilename -filter_complex "[0:v]scale=width=1030:height=580[scaled];[scaled]pad=w=1280:height=720:y=70[padded];[padded][1:v]overlay=x=1030:y=0[video]" -map "[video]" -map 0:1 -acodec copy -preset ultrafast $outputFilename

if ! ls $outputFilename > /dev/null 2>&1; then
    echo -e "\nVideo rendering failed.\n"
    exit
fi

echo -e "\n${bold}Done!${normal}\n"
