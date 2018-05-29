# Twitch Videochat

*Twitch VOD + chat replay in real time in the same video*

If you've ever watched a Twitch VOD/stream replay, you've probably noticed that Twitch displays a replay of the chat in real time alongside the video. It's pretty neat.

But what if you want to see the chat alongside the video, but don't want or can't watch it on Twitch?

While there are tools to download a Twitch video, and tools to download the chat replay in text form, I couldn't find a way to mix the two into the same video. That's what Twitch Videochat is for.

Give it a Twitch VOD URL, and it will create a new video with the stream on the left and the chat on the right. Here's what it looks like (with some stuff blurred for anonymity):

![Example](https://i.imgur.com/CUK55HO.png)

This can be useful if you want to watch a stream replay with chat on a device that doesn't support Twitch, or if you want to watch it offline. Or maybe you'd like to upload your replay on YouTube and want to allow YouTube viewers to see the chat without having to watch it on Twitch.

Usage:
- `./twitch_videochat.sh [URL to Twitch VOD]`. Example: `./twitch_videochat.sh https://www.twitch.tv/videos/123456789`
- You can speed up the frame generation phase with `--no-scrolling` (or just `-n`), as in `./twitch_videochat.sh --no-scrolling https://www.twitch.tv/videos/123456789`. This may make the chat less smooth and harder to follow, since new messages will suddenly appear at the bottom, but will greatly reduce the time needed to render all the necessary frames.
- The resulting video will be available in the `output` directory, inside a subdirectory named after the video ID.

What you need:
- This is a Bash script so you obviously need Bash or an equivalent.
- [youtube-dl](https://github.com/rg3/youtube-dl/) + [rechat-dl](https://github.com/KunaiFire/rechat-dl) which are provided as submodules.
- Python 3 + a few modules, notably PIL and tqdm.
- ffmpeg.
- (There may be some other requirements I forgot about, but you should be able to figure out what you're missing if you get an error.)

How it works:
- [youtube-dl](https://github.com/rg3/youtube-dl/) is used to download the Twitch video (actually it uses my wrapper [youtube-convert](https://github.com/Tailszefox/bin/blob/master/youtube-convert) which calls youtube-dl).
- [rechat-dl](https://github.com/KunaiFire/rechat-dl) is used to download the chat data in JSON.
- make_frames.py creates the frames that will be used to render the chat in video form.
- ffmpeg is used to create the final video. It resizes the original video, adds some space on the right for the chat, overlays it, and renders the final product.

Some caveats (actually a lot of them):
- I only tested this on my machine running Debian. It may or may not work depending on your environment.
- I only tested this with a handful of videos. It may or may not work with the video you want to use.
- It only works with videos from the "Video" tab on a Twitch channel.
- The process can take a while, depending on the amount of messages to process and the length of the video. As stated above, you can make the frame generation phase faster by using `--no-scrolling`, though this won't have an impact on the time necessary to render the final video.
- The final video is rendered in 720p because I was lazy and hardcoded all the dimensions. Everything bigger/smaller is scaled down/up.
- It only renders text. No emotes and no icons.
- I wouldn't try it with a video where the chat is hyperactive. The script won't have time to catch up and it will create an enormous amount of frames. If you still want to try, I strongly suggest using the `--no-scrolling` option.
- The script doesn't clean up after itself (so you can retry if there's an error). You'll have to delete the original video, chat and frames yourself once you're done.
- There may be something that I forgot that will cause your computer to explode or melt. You have been warned.

If that's all fine with you, have fun with Twitch Videochat!
