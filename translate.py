import deepl
import sys
import os
import requests
from collections import OrderedDict
from googletrans import Translator
# either get DeepL API key from sys env like so (on command line):
# export DEEPL_API_KEY=<your-deepl-key...>
DEEPL_AUTH_KEY = os.environ.get('DEEPL_API_KEY')
# or directly hard-code it here, like so:
#DEEPL_AUTH_KEY = "<your-deepl-key...>"

"""
A home-grown MT engine hosted through ngrok can easily be plugged in...
"""
#ngrok_url = "https://dae7-134-96-105-142.ngrok-free.app"
#english_to_pcm_url = f"{ngrok_url}/translate_english_to_pcm"


class DeepLTranslator:
    def __init__(self):
        self.translator = deepl.Translator(DEEPL_AUTH_KEY)
                                
    def translate(self, inp, trg):
        try:
            return self.translator.translate_text(inp, target_lang=trg).text
        except Exception as e:
            sys.stderr.write("ERROR: Failed to translate '%s': %s" % (inp, str(e)))


class GoogleTranslator:
    def __init__(self):
        self.translator = Translator()

    def translate(self, inp, trg):
        try:
            return self.translator.translate(inp, dest=trg).text
        except Exception as e:
            sys.stderr.write("ERROR: Failed to translate '%s': %s" % (inp, str(e)))


TRANSLATOR_MAPPING = OrderedDict(
    [
        ('deepl', DeepLTranslator),
        ("google", GoogleTranslator),
    ]
)


class AutoTranslator:
    @classmethod
    def get(self, translator_name):
        if translator_name in TRANSLATOR_MAPPING:
            return TRANSLATOR_MAPPING[translator_name]()
        raise ValueError(
            "Unrecognized translator api name {} for AutoTranslator: {}.\n"
            "Name should be one of {}.".format(
                ", ".join(c for c in TRANSLATOR_MAPPING.keys())
            )
        )


def main():
    api = "google"
    trans = AutoTranslator.get(api)

    inp = "Stocks have risen since last month. Although the economy is generally in decline."
    trg = 'de'
    inp = "Sanırım , bazıları coğrafı bölge ya da sokak ve bina topluluğu diyebilir ."
    trg = 'en'
    print(trans.translate(inp, trg))
    english_sentence = 'Process finished with exit code -1'
    english_to_pcm_payload = {"english_sentence": english_sentence}
    #pcm_translation_response = requests.post(english_to_pcm_url, json=english_to_pcm_payload)
    #pcm_translation = pcm_translation_response.json().get('pcm_translation', 'Translation error')
    #print('pcm translation:', pcm_translation)

if __name__ == '__main__':
    main()
