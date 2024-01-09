import os
import glob
import sys
import argparse
import custom_utils as cu
from dotenv import load_dotenv
from collections import namedtuple
import mimetypes
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc import Client, WordPressPost, WordPressMedia
from wordpress_xmlrpc.methods.posts import NewPost, EditPost
from wordpress_xmlrpc.methods.media import UploadFile
from wordpress_xmlrpc import Client, WordPressPost, WordPressTerm
from wordpress_xmlrpc.methods.posts import GetPosts, NewPost
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc.methods import media, posts
import requests
import re
from pprint import pprint

# Load environment variables from .env file
load_dotenv()

clogger = cu.instantiate_logger()

def upload_video_to_wordpress(video_path, wordpress_url, wordpress_username, wordpress_password):
    # Create a new session and authenticate with the WordPress site
    session = requests.Session()
    session.auth = (wordpress_username, wordpress_password)

    # Get the video filename and mime type
    video_filename = os.path.basename(video_path)
    mime_type, _ = mimetypes.guess_type(video_filename)

    # Upload the video to WordPress
    with open(video_path, 'rb') as video_file:
        clogger.debug(f"About to upload video: {video_path}")
        response = session.post(
            f'{wordpress_url}/wp-json/wp/v2/media',
            files={'file': (video_filename, video_file, mime_type)},
        )

    # Get the URL of the newly uploaded video
    #pprint(vars(response))
    response_json = response.json()
    video_url = response_json['guid']['rendered']

    return video_url

def set_post_thumbnail(wp_client, post_id, thumbnail_id):
    # Set the thumbnail for the post
    wp_client.call(posts.EditPost(post_id, {"post_thumbnail": thumbnail_id}))

def upload_image_to_wordpress(wp_client, image_path):
    # Read the image file
    with open(image_path, "rb") as img:
        image_data = img.read()

    # Get the file name and mime type
    file_name = os.path.basename(image_path)
    mime_type, _ = mimetypes.guess_type(image_path)

    # Create a media object and upload the image
    data = {
        'name': file_name,
        'type': mime_type,
        'bits': xmlrpc_client.Binary(image_data),
    }

    # Upload the image to WordPress
    uploaded_media = wp_client.call(media.UploadFile(data))

    return uploaded_media

def publish_wordpress_article(username, password, url, title, content, excerpt, tags=None, categories=None, post_status='publish'):
    """
    Publish an article to a WordPress website.

    Args:
        username (str): WordPress username.
        password (str): WordPress password.
        url (str): WordPress XML-RPC URL, usually in the format "https://your_website.com/xmlrpc.php".
        title (str): Post title.
        content (str): Post content.
        tags (list, optional): List of tags. Defaults to None.
        categories (list, optional): List of categories. Defaults to None.
        post_status (str, optional): Post status ('publish', 'draft', 'private', etc.). Defaults to 'publish'.
    """
    print(url)
    wp = Client(url, username, password)

    # Publish article
    post = WordPressPost()
    post.title = title
    post.content = content
    post.post_status = post_status
    post.excerpt = excerpt

    if tags:
        post.terms_names = {'post_tag': tags}
    if categories:
        post.terms_names = {'category': categories}

    post_id = wp.call(NewPost(post))

    image_path = "output-articles/article-thumb-notext.jpg"
    uploaded_media = upload_image_to_wordpress(wp, image_path)
    set_post_thumbnail(wp, post_id, uploaded_media["id"])

    post = wp.call(posts.GetPost(post_id))

    return post.link

def get_todays_date_in_spanish():
    today = datetime.date.today()
    formatted_date = format_date(today, "EEEE dd 'de' MMMM 'del' yyyy", locale='es')
    return formatted_date

def read_summary_and_title_files(base_dir):
    results = []

    def numeric_id(filename):
        return int(re.search(r'\d+', filename).group())

    # Iterate through all subdirectories in base_dir
    for subdir in os.listdir(base_dir):
        subdir_path = os.path.join(base_dir, subdir)

        if os.path.isdir(subdir_path):
            # Find all .txt.summary and .txt.title files in the subdirectory
            summary_files = glob.glob(os.path.join(subdir_path, '*.txt.summary'))
            title_files = glob.glob(os.path.join(subdir_path, '*.txt.title'))

            summary_files = sorted(summary_files, key=numeric_id)
            title_files = sorted(title_files, key=numeric_id)

            # Read the summary and title files and store them in a dictionary
            for summary_file, title_file in zip(summary_files, title_files):
                with open(summary_file, 'r', encoding='utf-8') as f_summary, open(title_file, 'r', encoding='utf-8') as f_title:
                    summary = f_summary.read().strip()
                    title = f_title.read().strip()

                    results.append({
                        'id': subdir,
                        'title': title,
                        'summary': summary
                    })

    return results


def main(args):
    url = os.getenv("WP_URL")
    username = os.getenv("WP_USERNAME")
    password = os.getenv("WP_PASSWORD")

    #current_date = cu.get_todays_date_in_spanish()
    #title = "Noticias destacadas del {}".format(current_date)
    title = cu.load_txt_files("output-articles", pattern="article-title.txt")[0]

    video_path = "output-articles/final-youtube-compressed.mp4"
    urn='biAIJdIK26iT82jxgy6KuQ'
    urn='dennis'
    pwd='vkx1 j2vH 9PfR gb95 5FJK PejF'
    ul='https://www.revistainformatica.com'
    #video_url = upload_video_to_wordpress(video_path, ul, urn, pwd)

    #clogger.debug(f"Video URL:: {video_url}")

    content = ''
    #content += f'[video width="1920" height="1080" mp4="{video_url}"][/video]'

    articles = read_summary_and_title_files('output-articles')
    for article in articles:
        if article['title'] and article['summary']:
            content += '<h3>{}</h3>'.format(article['title'])
            content += '\n'
            content += '<p>{}</p>'.format(article['summary'])
            content += '\n\n'

    post_link = publish_wordpress_article(username, password, url, title, content, title, None, ["noticia"], 'publish')
    cu.write_file(f"output-articles/", f"link.txt", post_link)
    print(post_link)
    clogger.debug(f"Post URL:: {post_link}")

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
