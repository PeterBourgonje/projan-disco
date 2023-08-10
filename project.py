import translate
import align
import discoparse
import json
import spacy
from operator import itemgetter
from itertools import groupby

def is_continuous(lst): 
    return all(a+1==b for a, b in zip(lst, lst[1:]))

def get_sequences(lst):
    seqs = []
    for k,g in groupby(enumerate(lst),lambda x:x[0]-x[1]):
        group = (map(itemgetter(1),g))
        group = list(map(int,group))
        seqs.append((group[0],group[-1]))
    return seqs

class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        self.aligner = align.Aligner()
        self.discopy = discoparse.Discopy()
        self.init_tokenizer()

    def init_tokenizer(self):
        nlp = spacy.load('xx_sent_ud_sm')
        self.tokenizer = spacy.tokenizer.Tokenizer(nlp.vocab)
        
    def annotate(self, inp, trans=False):
        if not trans:
            trans = self.translator.translate(inp, 'EN-US')
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
        
        projected_relations = []
        if 'relations' in parse:
            relations = parse['relations']
            for relation in relations:
                prel = {}
                for elem in relation:
                    if isinstance(relation[elem], dict) and 'CharacterSpanList' in relation[elem] and 'TokenList' in relation[elem]:
                        projected = {'CharacterSpanList': [], 'RawText': '', 'TokenList': []}
                        src_tokens = []
                        # not guaranteed that tokenization is identical between alignment and discopy, so have to go by char offsets
                        alt_tokens = []
                        for charspan in relation[elem]['CharacterSpanList']:
                            s, e = charspan[0], charspan[1]
                            for span in trans_o2t:
                                if s <= span[0] and span[1] <= e:
                                    alt_tokens.append(trans_o2t[span])
                        aligned_tokens = [[a[0] for a in alignments if a[1] == t] for t in alt_tokens]
                        aligned_tokens = sorted(list(set([t for tl in aligned_tokens for t in tl])))
                        if aligned_tokens:
                            projected['TokenList'] = aligned_tokens
                            if is_continuous(aligned_tokens):
                                s, e = inp_t2o[aligned_tokens[0]][0], inp_t2o[aligned_tokens[-1]][1]
                                projected['CharacterSpanList'] = [[s, e]]
                                projected['RawText'] = inp[s:e]
                            else:
                                seqs = get_sequences(aligned_tokens)
                                for seq in seqs:
                                    s, e = inp_t2o[seq[0]][0], inp_t2o[seq[-1]][1]
                                    projected['CharacterSpanList'].append([s, e])
                                    projected['RawText'] += ' ' + inp[s:e]
                                projected['RawText'] = projected['RawText'].strip()
                        prel[elem] = projected
                    else:
                        prel[elem] = relation[elem]
                projected_relations.append(prel)
        
        return projected_relations
                    
def main():
    # TODO: wrap annotate() in sentence loop
    inp = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'
    pd = ProjanDisco()
    pd.annotate(inp)
        
if __name__ == '__main__':
    main()
