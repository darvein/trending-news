import os
import sys
import argparse
import custom_utils as cu
from dotenv import load_dotenv
import os
import requests
import facebook

# Load environment variables from .env file
load_dotenv()

clogger = cu.instantiate_logger()

def upload_video_to_facebook(page_access_token, file_path, title, description):
    graph = facebook.GraphAPI(access_token=page_access_token, version="3.0")
    
    # Upload the video
    with open(file_path, "rb") as video_file:
        upload_response = graph.put_video(
            video_file,
            title=title,
            description=description
        )
    
    if "id" in upload_response:
        video_id = upload_response["id"]
        print(f"Video was successfully uploaded with video ID: {video_id}")
    else:
        print("The upload failed with an unexpected response:", upload_response)

def main(args):
    key_file_path = 'oauth-revistayoutube.json'
    youtube = get_authenticated_service(key_file_path)

    file_path = 'output-articles/final-youtube.mp4'
    title = cu.load_txt_files("output-articles", pattern="article-title.txt")[0].strip()
    description = cu.load_txt_files("output-articles", pattern="article-desc.txt")[0].strip()

    tags = ['revistainformatica', 'tecnologia', 'bolivia']
    category_id = '28'  # Science and technology
    privacy_status = 'unlisted'

    age_access_token = "your_page_access_token"
    file_path = "path/to/your/video.mp4"
    title = "Your Video Title"
    description = "Your Video Description"

    page_access_token = "your_page_access_token"

    try:
        upload_video_to_facebook(page_access_token, file_path, title, description)
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")

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
