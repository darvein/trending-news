import os
from PIL import Image
import math
import textwrap
import glob
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
import azure.cognitiveservices.speech as speechsdk
from moviepy.video.tools.drawing import circle
from moviepy.editor import *
import sys
import argparse
import custom_utils as cu
from dotenv import load_dotenv
from collections import namedtuple

load_dotenv()
clogger = cu.instantiate_logger()

def read_text_file(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    return text

def text_to_speech(text, output_file):
    try:
        voice_name='es-MX-NuriaNeural' # ella redacta

        # Set up the Azure Speech Service configuration
        speech_key = os.environ["AZURE_SPEECH_KEY"]
        speech_region = os.environ["AZURE_SPEECH_REGION"]

        # Create a SpeechSynthesizer instance
        speech_config = SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name = voice_name
        #speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_SynthOutputFormat, "riff-48khz-32bit-stereo-pcm")
        speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_SynthOutputFormat, "riff-16khz-16bit-mono-pcm")

        # Synthesize the text to speech
        audio_config = AudioConfig(filename=output_file)
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()

        print(result.reason)
        clogger.debug(f"Warn: {result.reason}")

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            clogger.debug(f"Warn: {cancellation_details}")
            clogger.debug(f"Warn: {cancellation_details.error_details}")
            sys.exit(1)
        else:
            # Save the synthesized speech to a file
            with open(output_file, "wb") as f:
                f.write(result.audio_data)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def create_video_with_images_and_audio(image_files, audio_file, title_text, output_file, text_font, zoom_percentage, video_width, video_height):
    # Load audio
    audio = AudioFileClip(audio_file)
    audio_duration = audio.duration

    # Calculate the duration for each image
    image_duration = audio_duration / len(image_files)

    # Load images and apply zoom effect
    clips = []
    for image_file in image_files:
        clip = ImageClip(image_file).set_duration(image_duration)
        
        # Calculate the zoom factor
        zoom_factor = lambda t: 1 + (zoom_percentage / 100) * (0.5 - 0.5 * math.cos(2 * math.pi * t / image_duration))
        
        clip = clip.fx(vfx.resize, zoom_factor)
        clips.append(clip)

    # Concatenate image clips
    video = concatenate_videoclips(clips, method="compose")

    # Set the audio to the video
    video = video.set_audio(audio)

    # Add title text clip
    title_size=100
    title_margin_x=10
    line_width = int((video_width - 2 * title_margin_x) / (title_size * 0.4))  # Calculate line_width based on video_width
    wrapped_text = textwrap.fill(title_text, width=line_width)
    title_clip = TextClip(wrapped_text, fontsize=title_size, color='white', bg_color='black', stroke_width=0, stroke_color='grey', font=text_font)
    title_clip = title_clip.set_position(('center', 'center'))
    title_clip = title_clip.set_duration(video.duration)

    # logo
    logo_file='./revista2.png'
    logo_clip = ImageClip(logo_file)
    logo_clip = logo_clip.resize((320, 200))
    logo_clip = logo_clip.set_pos(('right', 'top'))
    logo_clip = logo_clip.set_duration(video.duration)

    video = CompositeVideoClip([video, title_clip, logo_clip], size=(video_width, video_height))

    # Write the video file
    video.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=24)

def resize_and_center_image(image_path, width, height):
    img = Image.open(image_path)
    img_aspect_ratio = img.width / img.height
    new_width, new_height = width, int(width / img_aspect_ratio)

    if new_height < height:
        new_width, new_height = int(height * img_aspect_ratio), height

    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    centered_img = Image.new("RGB", (width, height), (0, 0, 0))
    x, y = (width - new_width) // 2, (height - new_height) // 2
    centered_img.paste(img, (x, y))

    centered_img.save(f"temp_{image_path}")
    return f"temp_{image_path}"

def resize_images(image_files, width, height):
    return [resize_and_center_image(image_path, width, height) for image_path in image_files]

def main(args):
    clusterid = args.clusterid

    text_file = "output-articles/{}/{}.txt.summary".format(clusterid, clusterid)
    title_file = "output-articles/{}/{}.txt.title".format(clusterid, clusterid)
    audio_file = f"speech-{clusterid}.wav"
    output_video_yt = "output-articles/{}/{}.yt.mp4".format(clusterid, clusterid)
    output_video_tt = "output-articles/{}/{}.tt.mp4".format(clusterid, clusterid)
    image_files = glob.glob("images/{}_*.jpg".format(clusterid))
    zooming = 100
    txt_font = 'FrontPageNeue.ttf'
    width_yt, height_yt = 1920, 1080
    width_tt, height_tt = 1080, 1920

    text = read_text_file(text_file)
    title_text = read_text_file(title_file)

    text_to_speech(text, audio_file)

    images_yt = resize_images(image_files, width_yt, height_yt)
    create_video_with_images_and_audio(images_yt, audio_file, title_text, output_video_yt, txt_font, zooming, width_yt, height_yt)

    images_tt = resize_images(image_files, width_tt, height_tt)
    create_video_with_images_and_audio(images_tt, audio_file, title_text, output_video_tt, txt_font, zooming, width_tt, height_tt)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video from a text file")
    parser.add_argument("clusterid", help="Cluster id of the data to generate a video")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
