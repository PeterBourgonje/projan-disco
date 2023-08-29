import deepl
import sys
import os
import requests

# export DEEPL_API_KEY=deepl-key...
DEEPL_AUTH_KEY = os.environ.get('DEEPL_API_KEY')

"""
Going with deepl for now, but this is where we'll want to insert Muhammed's MT engine...
"""
ngrok_url = "https://dae7-134-96-105-142.ngrok-free.app"
english_to_pcm_url = f"{ngrok_url}/translate_english_to_pcm"


class Translator:
    def __init__(self):
        self.translator = deepl.Translator(DEEPL_AUTH_KEY)

    def translate(self, inp, trg):
        try:
            return self.translator.translate_text(inp, target_lang=trg).text
        except Exception as e:
            sys.stderr.write("ERROR: Failed to translate '%s': %s" % (inp, str(e)))

def main():

    trans = Translator()
    #inp = "Stocks have risen since last month. Although the economy is generally in decline."
    #trg = 'de'
    #print(trans.translate(inp, trg))
    english_sentence = 'Process finished with exit code -1'
    english_to_pcm_payload = {"english_sentence": english_sentence}
    pcm_translation_response = requests.post(english_to_pcm_url, json=english_to_pcm_payload)
    pcm_translation = pcm_translation_response.json().get('pcm_translation', 'Translation error')
    print('pcm translation:', pcm_translation)

if __name__ == '__main__':
    main()
