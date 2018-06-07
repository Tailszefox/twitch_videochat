# Twitch Videochat

*Twitch VOD + chat replay in real time in the same video*

If you've ever watched a Twitch VOD/stream replay, you've probably noticed that Twitch displays a replay of the chat in real time alongside the video. It's pretty neat.

But what if you want to see the chat alongside the video, but don't want or can't watch it on Twitch?

While there are tools to download a Twitch video, and tools to download the chat replay in text form, I couldn't find a way to mix the two into the same video. That's what Twitch Videochat is for.

Give it a Twitch VOD URL, and it will create a new video with the stream on the left and the chat on the right. Here's what it looks like (with some stuff blurred for anonymity):

![Example](https://i.imgur.com/5jIdRao.png)

This can be useful if you want to watch a stream replay with chat on a device that doesn't support Twitch, or if you want to watch it offline. Or maybe you'd like to upload your replay on YouTube and want to allow YouTube viewers to see the chat without having to watch it on Twitch.

**Prerequisites**

You will need the following in order to run the script:
- Python 3.X. The script has been tested with Python 3.4 and 3.5.
- [youtube-dl](https://github.com/rg3/youtube-dl/) and [rechat-dl](https://github.com/KunaiFire/rechat-dl) are provided as submodules. If you've cloned the repository, you may need to issue the command `git submodule update --init --recursive` in order to actually download them.
- The following Python modules:
    - Pillow
    - tqdm
    - youtube-dl and rechat-dl may require you to install some additional modules
- ffmpeg and ffprobe. On Linux you should be able to install them through your usual package manager. On Windows, grab the latest Windows build from https://www.ffmpeg.org/download.html, and place ffmpeg.exe and ffprobe.exe in the same directory as the script itself.

If you're missing something else that's not in this list, you should get an error message telling you what.

**Usage**
- `./twitch_videochat.py [URL to Twitch VOD]` Example: `./twitch_videochat.py https://www.twitch.tv/videos/123456789`. On Windows you may need to call the script with `python twitch_videochat.py` instead.
- You can speed up the frame generation phase with `--no-scrolling`, as in `./twitch_videochat.py --no-scrolling https://www.twitch.tv/videos/123456789`. This may make the chat less smooth and harder to follow, since new messages will suddenly appear at the bottom, but will greatly reduce the time needed to render all the necessary frames.
- The resulting video will be available in the `output` directory, inside a subdirectory named after the video ID.

**How it works**
- [youtube-dl](https://github.com/rg3/youtube-dl/) is used to download the Twitch video.
- [rechat-dl](https://github.com/KunaiFire/rechat-dl) is used to download the chat data in JSON.
- The script parses the chat, renders frames for each message, and decides how long each frame should be displayed.
- ffmpeg is used to create the final video. The original video is resized and some room is added to the right. A new video is rendered using the frames created by the script, each frame being displayed for the amount of time the script has chosen. This video is then overlaid next to the original video, and the final video is rendered.

There's also a few things to keep in mind before you give it a shot:
- The script has been tested on Debian 8 and on Windows 10. It should work on most other OSes and flavors, but it might not.
- The script works with all the videos it's been tested with. If you do find a video that doesn't work, please open a new issue with a link to the video and a description of the problem.
- Only videos from the "Video" tab on a Twitch channel are compatible.
- The process can take a while, depending on the amount of messages to process and the length of the video. As stated above, you can make the frame generation phase faster by using `--no-scrolling`, though this won't have an impact on the time necessary to render the final video.
- Emotes and icons are not rendered. Emotes will only appear as text.
- Using the script on videos with an hyperactive chat (ie. a chat where there's dozens of new messages every second) is discouraged. You can try using the `--no-scrolling` option, but if the chat is really too fast for the script, it will never be able to catch up.
- The script doesn't clean up after itself (so you can retry if there's an error). You'll have to delete the original video, chat and frames yourself once you're done.
- As the script hasn't been extensively tested in a lot of environments, there's always the possibility that something will screw up royally. The chances that your computer will explode are slim, but still, you've been warned.

If that's all fine with you, have fun with Twitch Videochat!
