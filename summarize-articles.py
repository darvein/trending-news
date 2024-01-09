import sys
import os
from transformers import BartTokenizer, TFBartForConditionalGeneration, MarianTokenizer, TFMarianMTModel
from langdetect import detect
import custom_utils as cu
import argparse
import nltk

nltk.download('punkt')

clogger = cu.instantiate_logger()

def generate_summary(model, tokenizer, text):
    text = cu.cleanup_text(text)

    # Increase max_length for tokenizing input to handle longer documents
    #inputs = tokenizer([text], max_length=7000, return_tensors="tf", truncation=True)
    inputs = tokenizer([text], max_length=3000, return_tensors="tf", truncation=True)
    
    # Increase max_length for generating output to create longer summaries
    #outputs = model.generate(inputs["input_ids"], max_length=3000, min_length=200, num_beams=4, early_stopping=True)
    outputs = model.generate(inputs["input_ids"], max_length=1500, min_length=100, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Post-process summary to remove the last incomplete sentence
    sentences = nltk.tokenize.sent_tokenize(summary)
    if not sentences[-1].endswith(('.', '!', '?')):
        sentences = sentences[:-1]
        print(f"ALERT: incomplete::: {sentences}")

    summary = ' '.join(sentences)

    return summary


def translate_to_english(text):
    model_name = "Helsinki-NLP/opus-mt-es-en"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = TFMarianMTModel.from_pretrained(model_name)

    inputs = tokenizer(text, return_tensors="tf", padding=True, truncation=True)
    outputs = model.generate(**inputs)
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)

    return translation

def main(args):
    summary_model = TFBartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
    summary_tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

    clusterid = args.clusterid
    directorypath = f"output-articles/{clusterid}"
    txt_files = cu.load_txt_files(directorypath, '.txt')
    clogger.debug(f"Loaded txt files from: {directorypath}")

    if len(txt_files) == 0:
        clogger.error("No files found at {}".format(directorypath))
        sys.exit(1)

    summaries = []
    for text in txt_files:
        if len(text) >= 180:
            # TODO No need to translate spanish summaries to english
            #lang = detect(text)
            #if lang == 'es':
                #text = translate_to_english(text)
            summary = generate_summary(summary_model, summary_tokenizer, text)
            
            if summary:
                clogger.debug(f"Summary so far...: {summary}")
                summaries.append(summary)

    summaries_text = " ".join(summaries)
    final_summary = generate_summary(summary_model, summary_tokenizer, summaries_text)

    final_summary_spanish = cu.translate_to_spanish(final_summary)

    clogger.debug(final_summary_spanish)
    cu.write_file(directorypath, f"{clusterid}.txt.summary", final_summary_spanish)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize articles")
    parser.add_argument("clusterid", help="Cluster id folder")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()
    
    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
