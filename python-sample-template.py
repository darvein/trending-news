import os
import sys
import argparse
import custom_utils as cu
from dotenv import load_dotenv
from collections import namedtuple

# Load environment variables from .env file
load_dotenv()

clogger = cu.instantiate_logger()

# Define a namedtuple to store the results
FileStats = namedtuple("FileStats", ["lines", "words", "characters"])

def count_file_stats(file_path, extra_string):
    with open(file_path, "r") as file:
        lines = 0
        words = 0
        characters = 0

        for line in file:
            lines += 1
            words += len(line.split())
            characters += len(line)

    clogger.debug(f"Extra string: {extra_string}")

    return FileStats(lines=lines, words=words, characters=characters)

def main(args):
    file_stats = count_file_stats(args.file_path, args.extra_string)
    print(f"File: {args.file_path}")
    print(f"Lines: {file_stats.lines}")
    print(f"Words: {file_stats.words}")
    print(f"Characters: {file_stats.characters}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count the number of lines, words, and characters in a file.")
    parser.add_argument("file_path", help="Path to the input file.")
    parser.add_argument("extra_string", help="An additional string.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.debug: clogger.setLevel(cu.LOG_DEBUG)

    # Read an environment variable from the .env file
    env_var = os.getenv("MY_ENV_VARIABLE")
    clogger.debug(f"Environment variable: {env_var}")

    try:
        main(args)
    except Exception as e:
        clogger.error(f"Error: {e}")
        sys.exit(1)
