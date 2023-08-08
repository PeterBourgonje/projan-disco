import translate
import align
import discoparse
import json
import spacy


class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        self.aligner = align.Aligner()
        self.discopy = discoparse.Discopy()
        self.init_tokenizer()

    def init_tokenizer(self):
        nlp = spacy.load('xx_sent_ud_sm')
        self.tokenizer = spacy.tokenizer.Tokenizer(nlp.vocab)
        
    def annotate(self, inp):
        #trans = self.translator.translate(inp, 'EN-US')
        trans = 'Stock prices have risen since last month. Although the economy is generally declining.'
        parse = json.loads(self.discopy.parse(trans))
        # discopy seems to change input text (inserting newlines for ex.), so working with RawText coming back from discopy from here
        trans = parse['text']
        
        inp_tokenized = self.tokenizer(inp)
        trans_tokenized = self.tokenizer(trans)
        alignments = self.aligner.align([t.text for t in inp_tokenized], [t.text for t in trans_tokenized])['mwmf']
        inp_t2o = {t.i: (t.idx, t.idx+len(t.text)) for t in inp_tokenized}
        trans_t2o = {t.i: (t.idx, t.idx+len(t.text)) for t in trans_tokenized}
        inp_o2t = {(t.idx, t.idx+len(t.text)): t.i for t in inp_tokenized}
        trans_o2t = {(t.idx, t.idx+len(t.text)): t.i for t in trans_tokenized}
        print('deb alignments:', alignments)
        
        projected_relations = []
        if 'relations' in parse:
            relations = parse['relations']
            for relation in relations:
                print('debrel:', relation)
                prel = {}
                for elem in relation:
                    print('\tdeb elem:', elem)
                    print('\t\tdeb cont:', relation[elem])
                    if isinstance(relation[elem], dict) and 'CharacterSpanList' in relation[elem] and 'TokenList' in relation[elem]:
                        projected = {'CharacterSpanList': [], 'RawText': '', 'TokenList': []}
                        src_tokens = []
                        # not guaranteed that tokenization is identical between alignment and discopy, so have to go by char offsets
                        al_tokens = []
                        for charspan in relation[elem]['CharacterSpanList']:
                            s, e = charspan[0], charspan[1]
                            for span in trans_o2t:
                                if s <= span[0] and span[1] <= e:
                                    al_tokens.append(trans_o2t[span])
                        print('deb altokens:', al_tokens)
                        # TODO: have the aligned tokens here in al_tokens. Now use alignments to get the tokens on the pidgin/src text side, then figure out if that is a discontinuous array, then get charspanlists from there, and then it should be round-tripped.
                        prel[elem] = projected
                    else:
                        prel[elem] = relation[elem]
                projected_relations.append(prel)
        print('Projected relations:', projected_relations)
                    
def main():
    # TODO: wrap annotate() in sentence loop
    inp = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'
    pd = ProjanDisco()
    pd.annotate(inp)
        
if __name__ == '__main__':
    main()
