import deepl
import sys
import os

# export DEEPL_API_KEY=deepl-key...
DEEPL_AUTH_KEY = os.environ.get('DEEPL_API_KEY')

"""
Going with deepl for now, but this is where we'll want to insert Muhammed's MT engine...
"""

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
    inp = "Stocks have risen since last month. Although the economy is generally in decline."
    trg = 'de'
    print(trans.translate(inp, trg))
    
if __name__ == '__main__':
    main()
