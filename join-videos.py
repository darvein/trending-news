import os
import re
import sys
import glob
import argparse
import numpy as np
import custom_utils as cu
from dotenv import load_dotenv
from collections import namedtuple
from moviepy.editor import AudioFileClip, afx, VideoFileClip, concatenate_videoclips
from moviepy.editor import ColorClip, CompositeAudioClip
from moviepy.audio.AudioClip import AudioArrayClip

# Load environment variables from .env file
load_dotenv()

clogger = cu.instantiate_logger()

def join_videos(file_pattern, additional_video, output_video, background_music):
    video_files = glob.glob(file_pattern)

    volume_factor = 1.8
    music_volume = 0.2  # 30% lower volume
    pause_duration = 0.5  # 1.5 seconds of dead time
    fade_duration = 1  # 1 second of fade-in and fade-out

    # Extract numeric ID from the filename and use it as a sorting key
    def numeric_id(filename):
        return int(re.search(r'\d+', filename).group())

    # Sort video_files by numeric ID
    sorted_video_files = sorted(video_files, key=numeric_id)

    video_clips = [VideoFileClip(video_file).volumex(volume_factor) for video_file in sorted_video_files]

    # Add dead time between video clips
    black_clip = ColorClip(size=video_clips[0].size, color=(0,0,0), duration=pause_duration)
    video_clips = [clip for pair in zip([black_clip] * len(video_clips), video_clips) for clip in pair][1:]

    # Add the additional video to the list of video clips
    additional_video_clip = VideoFileClip(additional_video)
    video_clips.insert(0, additional_video_clip)  # Insert at the beginning

    # Add fade-in and fade-out transitions to sorted_video_files clips
    video_clips[1:] = [clip.crossfadein(fade_duration).crossfadeout(fade_duration) for clip in video_clips[1:]]

    # Concatenate video clips
    final_video = concatenate_videoclips(video_clips)

    # Add background music
    background_music_clip = AudioFileClip(background_music).volumex(music_volume)
    bgm_duration = sum([clip.duration for clip in video_clips])
    background_music_clip = afx.audio_loop(background_music_clip, duration=bgm_duration)
    final_audio = CompositeAudioClip([final_video.audio.set_end(bgm_duration), background_music_clip])
    final_video = final_video.set_audio(final_audio)

    # Write the output video
    final_video.write_videofile(output_video)

def main(args):
    youtube_path = 'output-articles/**/*.yt.mp4'
    tiktok_path = 'output-articles/**/*.tt.mp4'

    youtube_output = 'output-articles/final-youtube.mp4'
    tiktok_output = 'output-articles/final-tiktok.mp4'

    background_music = 'futuristic.mp3'

    join_videos(youtube_path, "youtube-intro.mp4", youtube_output, background_music)
    join_videos(tiktok_path, "tiktok-intro.mp4", tiktok_output, background_music)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count the number of lines, words, and characters in a file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
