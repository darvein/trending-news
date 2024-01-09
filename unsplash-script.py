import os
import sys
import random
import requests
import argparse
from io import BytesIO
from dotenv import load_dotenv
from colorthief import ColorThief
from PIL import Image
import os
import math
import glob
import custom_utils as cu

load_dotenv()
clogger = cu.instantiate_logger()

def create_collage(file_pattern, output_image, output_image_notext, overlay_image_path, collage_size=(1280, 720)):
    images = glob.glob(file_pattern)
    random.shuffle(images)

    # If 'images' has less than 15 items, randomly repeat items to make the array at least 15 items
    while len(images) < 9:
        random_image = random.choice(images)
        images.append(random_image)

    #images = images[:9] # for real thumbnails
    images = images[:4]
    img_count = len(images)

    collage = Image.new('RGB', collage_size, color=(255, 255, 255))

    grid_size = int(math.sqrt(img_count))
    while img_count % grid_size != 0:
        grid_size -= 1

    rows = grid_size
    cols = img_count // grid_size

    cell_width = collage_size[0] // cols
    cell_height = collage_size[1] // rows

    img_idx = 0
    for row in range(rows):
        for col in range(cols):
            img = Image.open(images[img_idx])
            img = img.resize((cell_width, cell_height))

            x_offset = col * cell_width
            y_offset = row * cell_height
            collage.paste(img, (x_offset, y_offset))

            img_idx += 1
            if img_idx >= img_count:
                break

    # Add the overlay image on top of the collage
    overlay = Image.open(overlay_image_path).convert('RGBA')
    overlay = overlay.resize(collage_size)

    # Convert the final image back to 'RGB' mode before saving as JPEG
    collage_rgba = collage.convert('RGBA')
    collage_with_overlay = Image.alpha_composite(collage_rgba, overlay)


    collage_rgba = collage_rgba.convert('RGB')
    collage_rgba.save(output_image_notext, format="JPEG")

    collage_with_overlay_rgb = collage_with_overlay.convert('RGB')
    collage_with_overlay_rgb.save(output_image, format="JPEG")

def search_photos(query, per_page=5, page=1):
    # Read an environment variable from the .env file
    UNSPLASH_API_URL = os.getenv("UNSPLASH_API_URL")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

    url = f'{UNSPLASH_API_URL}search/photos'
    headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
    params = {
        'query': query,
        'per_page': per_page,
        'page': page
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    resized_image_urls = []
    for result in data['results']:
        original_url = result['urls']['raw']
        resized_url = f"{original_url}&w=1920&h=1080&fit=crop"
        resized_image_urls.append(resized_url)

    #random.shuffle(resized_image_urls)
    return resized_image_urls


def extract_entities(title):
    chunked = ne_chunk(pos_tag(word_tokenize(title)))
    entities = []
    
    for i in chunked:
        if isinstance(i, Tree):
            entity_type = i.label()
            entity_name = " ".join([token for token, pos in i.leaves()])
            entities.append((entity_name, entity_type))
    
    return entities


def download_image(url, filename, width=1920, height=1080):
    # Add the width and height parameters to the URL
    url = f"{url}&w={width}&h={height}"
    response = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(response.content)

def get_subdirectories(directory):
    subdirs = [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]
    return subdirs

def main(args):
    directory_path = './output-articles'
    subdirectories = get_subdirectories(directory_path)
    subdirectories = sorted(subdirectories)

    for clusterid in subdirectories:
        query = ""

        file_path = f"output-articles/{clusterid}/{clusterid}.txt.image"
        with open(file_path, 'r') as file:
            query = file.readline().strip()  # Reads one line and removes the newline character

        clogger.debug("Getting image for: {}: {}".format(clusterid, query))

        # Download photos
        # TODO: Remove this
        query="abstract"
        results = search_photos(query)
        for idx, url in enumerate(results[:2]):
            file_name = f'images/{clusterid}_{idx}.jpg'
            download_image(url, file_name)
            clogger.debug(f'Downloaded {file_name}')

    # Generate thumbnail
    image_directory = "./images/*.jpg"
    output_file = "output-articles/article-thumb.jpg"
    output_image_notext = "output-articles/article-thumb-notext.jpg"
    overlay_file = "./revista-title-thum.png"
    create_collage(image_directory, output_file, output_image_notext, overlay_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download images from unsplash")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
