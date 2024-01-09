import openai
import os
import sys

class ChatApp:
    def __init__(self, model="gpt-4", load_file=''):
        # Setting the API key to use the OpenAI API
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.messages = []
        if load_file != '':
            self.load(load_file)

    def chat(self, message):
        if message == "save":
            self.save()
            return "(saved)"

        self.messages.append({"role": "user", "content": message})
        self.messages.append({"role": "system", "content" : "You’re a kind helpful assistant"})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages,
        )

        self.messages.append({"role": "assistant", "content": response["choices"][0]["message"].content})
        return response["choices"][0]["message"]["content"]

    def save(self):
        try:
            import time
            import re
            import json
            ts = time.time()
            json_object = json.dumps(self.messages, indent=4)
            filename_prefix=self.messages[0]['content'][0:30]
            filename_prefix = re.sub('[^0-9a-zA-Z]+', '-', f"{filename_prefix}_{ts}")
            with open(f"models/chat_model_{filename_prefix}.json", "w") as outfile:
                outfile.write(json_object)
        except:
            os._exit(1)

    def load(self, load_file):
        with open(load_file) as f:
            data = json.load(f)
            self.messages = data

if __name__ == '__main__':
    prompt = sys.argv[1] if len(sys.argv)>1 else []
    if not sys.stdin.isatty():
        prompt = sys.stdin.read()

    app = ChatApp(model="gpt-4")
    response = app.chat(prompt)
    print(response)
