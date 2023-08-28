import translate
import align
import discoparse
import json
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

def get_token2offsets(sentlist, txt):
    t2o = {}
    c_offset = 0
    ti = 0
    for sent in sentlist:
        for t in sent.split():
            t2o[ti] = (c_offset, c_offset + len(t))
            assert txt[c_offset:c_offset + len(t)] == t
            ti += 1
            c_offset += len(t) + 1
    return t2o

def get_offsets2token(sentlist, txt):
    o2t = {}
    c_offset = 0
    ti = 0
    for sent in sentlist:
        for t in sent.split():
            o2t[(c_offset, c_offset + len(t))] = ti
            assert txt[c_offset:c_offset + len(t)] == t
            ti += 1
            c_offset += len(t) + 1
    return o2t

class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        self.aligner = align.Aligner()
        self.discopy = discoparse.Discopy()

    def annotate(self, inp, trans):

        assert isinstance(inp, list)
        assert isinstance(trans, list)
        parse_input = ' '.join(trans)
        orig_input = ' '.join(inp)
        parse = json.loads(self.discopy.parse(parse_input))
        assert parse_input == parse['text'], "Input text does not match text coming back from discopy. \nInput:\n%s\nDiscopy return text:\n%s" % ('\n'.join(trans), parse['text'])

        # Since translation is done sentence-by-sentence, number of sentences in srg and trg text should be the same
        assert len(inp) == len(trans)
        # Note that input is assumed to be pretokenized (white-space tokenized).
        inp_t2o = get_token2offsets(inp, orig_input)
        trans_o2t = get_offsets2token(trans, parse_input)

        alignments = self.aligner.align_sentences(inp, trans)

        projected_relations = []
        if 'relations' in parse:
            relations = parse['relations']
            for relation in relations:
                prel = {}
                for elem in relation:
                    if isinstance(relation[elem], dict) and 'CharacterSpanList' in relation[elem] and 'TokenList' in relation[elem]:
                        projected = {'CharacterSpanList': [], 'RawText': '', 'TokenList': []}
                        #src_tokens = []
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
                                #projected['RawText'] = inp[s:e]
                                projected['RawText'] = orig_input[s:e]
                            else:
                                seqs = get_sequences(aligned_tokens)
                                for seq in seqs:
                                    s, e = inp_t2o[seq[0]][0], inp_t2o[seq[-1]][1]
                                    projected['CharacterSpanList'].append([s, e])
                                    #projected['RawText'] += ' ' + inp[s:e]
                                    projected['RawText'] += ' ' + orig_input[s:e]
                                projected['RawText'] = projected['RawText'].strip()
                        prel[elem] = projected
                    else:
                        prel[elem] = relation[elem]
                projected_relations.append(prel)
        
        return projected_relations
                    
def main():
    
    inp = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'
    trans = 'Stock prices have risen since last month. Although the economy is generally declining.' # would normally get this from translator
    pd = ProjanDisco()
    pd.annotate(inp, trans)
        
if __name__ == '__main__':
    main()