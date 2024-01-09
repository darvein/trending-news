import os
import re
from openai import OpenAI
import hashlib
import logging
import colorlog
import time
from pprint import pprint
from newspaper import Article, Config, ArticleException
import datetime
from babel.dates import format_date

import os
import sys

AZURE_SUBSCRIPTION_KEY=""

class ChatApp:
    def __init__(self, model="gpt-4-1106-preview"):
        self.model = model
        self.messages = []

    def chat(self, message):
        client = OpenAI()

        prompt = self.format_messages_for_prompt(self.messages)
        completion = client.chat.completions.create(
            model=self.model,
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1000,  # You can adjust this value
            temperature=0.7  # You can adjust this value
        )

        return completion.choices[0].message.content

    def format_messages_for_prompt(self, messages):
        formatted_messages = []
        for message in messages:
            formatted_messages.append(f"{message['role'].capitalize()}: {message['content']}")
        return "\n".join(formatted_messages)

# Azure
subscription_key = AZURE_SUBSCRIPTION_KEY
region = "eastus"

LOG_DEBUG = logging.DEBUG
BLACK_LIST_CHATGPT = ["", "I am happy", "My name is John", "Estoy feliz", "Eres un asistente amable y servicial."]

def get_todays_date_in_spanish():
    today = datetime.date.today()
    formatted_date = format_date(today, "EEEE dd 'de' MMMM 'del' yyyy", locale='es')
    return formatted_date

def instantiate_logger():
    log_format = (
        "%(asctime)s - %(levelname)s - %(name)s - "
        "%(log_color)s%(message)s%(reset)s"
    )

    logging.basicConfig(level=logging.INFO, format=log_format)
    colorlog.basicConfig(level=logging.INFO, format=log_format)
    logger = colorlog.getLogger(__name__)

    return logger


def write_file(dirpath, filename, content):
    # Check if the directory does not exist
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)

    with open(f"{dirpath}/{filename}", 'w') as file:
        file.write(content)

def hash_file_title(title, clusterid):
    directory_name = f"output-articles/{clusterid}"

    # Check if the directory does not exist
    if not os.path.exists(directory_name):
        os.mkdir(directory_name)

    hashed_title = hashlib.md5(title.encode()).hexdigest()
    filename = f"./{directory_name}/{hashed_title}.txt"

    return filename

def load_txt_files(directory, pattern=".txt"):
    txt_files = []
    for file in os.listdir(directory):
        if file.endswith(pattern):
            with open(os.path.join(directory, file), "r") as f:
                txt_files.append(f.read())

    return txt_files


#article_body = get_article_text(entry.link, entry.title)
def get_article_text(url, title, clusterid):
    print(f"Downloading: {url}")
    text = ''

    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'

    try:
        article = Article(url, config=config)
        article.download()
        article.parse()
        text = article.text
    except ArticleException:
        print("Not able to download: {}".format(url))

    if text:
        output_file = hash_file_title(title, clusterid)
        with open(output_file, 'w') as file:
            file.write(text)

    return text

def cleanup_text(s):
    clean = s
    clean = re.sub(r'^[^a-zA-Z0-9]+', '', s)
    clean = clean.strip()
    return clean

def translate_to_spanish(text):
    output = ""

    while output in BLACK_LIST_CHATGPT:
        try:
            app = ChatApp(model="gpt-4")
            output = app.chat(f"Translate the following English text to Spanish:\n\n{text}\n")
        except Exception as e:
            print(f"Error during translation: {e}")
            time.sleep(5)

    return output

def call_chatgpt(prompt, max_tokens=2048, temperature=0.4):
    output = ""

    while output in BLACK_LIST_CHATGPT:
        try:
            app = ChatApp(model="gpt-4")
            output = app.chat(prompt)
        except Exception as e:
            print(f"Error during translation: {e}")
            time.sleep(5)

    return output

def extract_important_keywords(text):
    output = ""

    while output in BLACK_LIST_CHATGPT:
        try:
            app = ChatApp(model="gpt-4")
            output = app.chat(f"Get the main entity in 1 to 2 words from this setence:\n\n{text}\n")
        except Exception as e:
            print(f"Error during translation: {e}")
            time.sleep(5)

    return output

def cprint(obj):
    pprint(obj)
