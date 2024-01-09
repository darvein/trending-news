import re
import sys
import json
import nltk
import argparse
import tldextract
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

import custom_utils as cu

clogger = cu.instantiate_logger()

SIMILARITY_THRESHOLD = 0.30
MIN_UNIQUE_DOMAINS = 4

nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("punkt")

def download_article(news_obj, title, cluster_id):
    domain = f"{tldextract.extract(news_obj['url']).domain}.{tldextract.extract(news_obj['url']).suffix}"
    
    if domain not in ['twitter.com', 'reddit.com', 'www.nytimes.com']:
        return cu.get_article_text(news_obj['url'], title, cluster_id)
    else:
        return None

def preprocess_title(title):
    tokens = nltk.word_tokenize(title.lower())
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    clean_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words]
    return " ".join(clean_tokens)

def unique_domains(urls):
    return set(f"{ext.subdomain}.{ext.domain}.{ext.suffix}".lstrip('.') for url in urls for ext in (tldextract.extract(url),))

def load_titles_from_file(file_path):
    with open(file_path, "r") as f:
        news_objects = json.load(f)
    return [item['title'] for item in news_objects]

def compute_tfidf_matrix(titles):
    preprocessed_titles = [preprocess_title(title) for title in titles]
    vectorizer = TfidfVectorizer()
    return vectorizer.fit_transform(preprocessed_titles)

def compute_similarity_matrix(tfidf_matrix):
    return cosine_similarity(tfidf_matrix)

def cluster_titles(similarity_matrix, titles, news_objects):
    clusters = {}
    visited_titles = set()
    visited_urls = set()

    for i, title in enumerate(titles):
        if i in visited_titles:
            continue

        news_obj = next(item for item in news_objects if item['title'] == title)
        url = news_obj['url']

        if url in visited_urls:
            continue

        cluster = [title]
        visited_titles.add(i)
        visited_urls.add(url)

        for j, other_title in enumerate(titles):
            if j != i and j not in visited_titles and similarity_matrix[i][j] >= SIMILARITY_THRESHOLD:
                other_news_obj = next(item for item in news_objects if item['title'] == other_title)
                other_url = other_news_obj['url']

                if other_url not in visited_urls:
                    cluster.append(other_title)
                    visited_titles.add(j)
                    visited_urls.add(other_url)

        clusters[len(clusters)] = cluster
    return clusters

def filter_and_sort_clusters(clusters, news_objects):
    filtered_clusters = {
        cluster_id: titles
        for cluster_id, titles in clusters.items()
        if len(unique_domains([item['url'] for item in news_objects if item['title'] in titles])) >= MIN_UNIQUE_DOMAINS
    }
    sorted_clusters = sorted(
        filtered_clusters.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    return sorted_clusters

def download_articles(sorted_clusters, news_objects):
    for cluster_id, titles in sorted_clusters.items():
        with ThreadPoolExecutor(max_workers=5) as executor:
            news_objects_list = [next(item for item in news_objects if item['title'] == title) for title in titles]
            results = list(executor.map(download_article, news_objects_list, titles, [cluster_id] * len(titles)))

def main(args):
    news_objects = None
    with open("out-titles-news.json", "r") as f:
        news_objects = json.load(f)

    news_titles = load_titles_from_file("out-titles-news.json")
    tfidf_matrix = compute_tfidf_matrix(news_titles)
    similarity_matrix = compute_similarity_matrix(tfidf_matrix)
    clusters = cluster_titles(similarity_matrix, news_titles, news_objects)
    sorted_clusters = filter_and_sort_clusters(clusters, news_objects)

    # TODO Number of news
    if len(sorted_clusters) > 8: 
        sorted_clusters = sorted_clusters[0:8]

    renumbered_clusters = {i + 1: titles for i, (_, titles) in enumerate(sorted_clusters)}

    for cluster_id, titles in renumbered_clusters.items():
        print(f"Cluster {cluster_id}:")

        domains_list = []
        bunch_titles = ""
        for title in titles:
            news_obj = next(item for item in news_objects if item['title'] == title)

            bunch_titles += ("- " + title + "\n")
            print(f"- {title} ({news_obj['url']})")

            parsed_url = urlparse(news_obj['url'])
            domains_list.append(parsed_url.netloc)

        clogger.debug("{} Domains found.".format(len(set(domains_list))))
#
        prompt_text = f"Give me a summarized title from the following list of titles, keep in mind that an ideal article has 50 to 60 characters:\n\n{bunch_titles}"
#
        summarized_title = cu.call_chatgpt(prompt_text)
        clogger.debug(f"Summary title English: {summarized_title}")

        main_keywords = cu.extract_important_keywords(summarized_title)

        summarized_title = cu.translate_to_spanish(summarized_title)
        summarized_title = summarized_title.replace('"', '')
        clogger.debug(f"Summary title Spanish: {summarized_title}")

        cu.write_file(f"output-articles/{cluster_id}", f"{cluster_id}.txt.title", summarized_title)
        cu.write_file(f"output-articles/{cluster_id}", f"{cluster_id}.txt.image", main_keywords)
        print("\n")

    download_articles(renumbered_clusters, news_objects)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clusterize and organize news")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
