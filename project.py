import translate
import align
import discoparse
import json
from nltk.tokenize import word_tokenize # taking simple nltk tokenizer to support low-res langs

class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        self.aligner = align.Aligner()
        self.discopy = discoparse.Discopy()
    
        
    def annotate(self, inp):
        #translation = self.translator.translate(inp, 'EN-US')
        translation = 'Stock prices have risen since last month. Although the economy is generally declining.'
        alignments = self.aligner.align(word_tokenize(inp), word_tokenize(translation))['mwmf']
        print(alignments)
        # TODO: make sure tokenization is identical (seems to be a tokenization endpoint in discopy, figure out if that can be called using the api)
        parse = json.loads(self.discopy.parse(translation))
        if 'relations' in parse:
            relations = parse['relations']
            for relation in relations:
                print('debrel:', relation)

        
def main():
    inp = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'
    pd = ProjanDisco()
    pd.annotate(inp)
        
if __name__ == '__main__':
    main()
