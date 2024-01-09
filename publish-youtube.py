import os
import sys
import argparse
import custom_utils as cu
import googleapiclient.errors
from dotenv import load_dotenv
import googleapiclient.discovery
import google_auth_oauthlib.flow
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import pickle
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

clogger = cu.instantiate_logger()

def get_authenticated_service2(client_secrets_file):
    credentials_file = client_secrets_file + ".pickle"

    scopes = ["https://www.googleapis.com/auth/youtube.upload"]

    credentials = None

    # Check if the credentials file exists and load the credentials
    if os.path.exists(credentials_file):
        with open(credentials_file, "rb") as f:
            credentials = pickle.load(f)

    # If the credentials are not available or invalid, run the OAuth flow
    if not credentials or not credentials.valid:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
        credentials = flow.run_local_server(port=0)

        # Save the credentials to a file for future use
        with open(credentials_file, "wb") as f:
            pickle.dump(credentials, f)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    return youtube


def get_authenticated_service(client_secrets_file):
    credentials_file = client_secrets_file + ".pickle"
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    credentials = None
    # Check if the credentials file exists and load the credentials
    if os.path.exists(credentials_file):
        with open(credentials_file, "rb") as f:
            credentials = pickle.load(f)
    # If the credentials are not available or expired, run the OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            credentials = flow.run_console()  # Use run_console instead of run_local_server

        # Save the credentials to a file for future use
        with open(credentials_file, "wb") as f:
            pickle.dump(credentials, f)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)
    return youtube

def upload_video(youtube, file_path, title, description, tags, category_id, privacy_status):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    # Upload the video
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype='video/*')
    request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
    response = None

    while response is None:
        status, response = request.next_chunk()
        if 'id' in response:
            print(f"Video was successfully uploaded with video ID: {response['id']}")
        else:
            print("The upload failed with an unexpected response:", response)

def main(args):
    key_file_path = 'oauth-revistayoutube.json'
    youtube = get_authenticated_service(key_file_path)

    file_path = 'output-articles/final-youtube.mp4'
    title = cu.load_txt_files("output-articles", pattern="article-title.txt")[0].strip()
    title = title[:100]

    tags = ['revistainformatica', 'tecnologia', 'bolivia']
    category_id = '28'  # Science and technology
    privacy_status = 'public'

    article_link = cu.load_txt_files("output-articles", pattern="link.txt")[0].strip()
    tags_string = ' '.join(['#' + tag for tag in tags])
    description = f"{title}\n{article_link}\n{tags_string}"


    try:
        upload_video(youtube, file_path, title, description, tags, category_id, privacy_status)
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
