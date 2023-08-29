import translate
import align
import discoparse
import json


class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        self.aligner = align.Aligner()
        self.discopy = discoparse.Discopy()

    def annotate(self, inp, trans):

        # checking that input is pre-sentencized and pre-tokenized
        assert isinstance(inp, list)
        assert isinstance(trans, list)
        assert all(isinstance(x, list) for x in inp)
        assert all(isinstance(x, list) for x in trans)
        discopy_response = json.loads(self.discopy.parse(trans))

        # Since translation is done sentence-by-sentence, number of sentences in srg and trg text should be the same
        assert len(inp) == len(trans)
        alignments = self.aligner.align_sentences(inp, trans)
        id2token = {}
        tid = 0
        for sent in inp:
            for token in sent:
                id2token[tid] = token
                tid += 1
        """
        trans_id2token = {}  # for debugging purposes
        tid = 0
        for sent in trans:
            for token in sent:
                trans_id2token[tid] = token
                tid += 1
        """
        projected_relations = []
        if 'relations' in discopy_response:
            relations = discopy_response['relations']
            for relation in relations:
                prel = {}
                for elem in relation:
                    # ignoring CharacterSpanList altogether
                    if isinstance(relation[elem], dict) and 'TokenList' in relation[elem]:
                        aligned_tokens = [[a[0] for a in alignments if a[1] == t] for t in relation[elem]['TokenList']]
                        aligned_tokens = sorted(list(set([t for tl in aligned_tokens for t in tl])))
                        rawtext = ' '.join([id2token[i] for i in aligned_tokens]).strip()
                        projected = {'RawText': rawtext, 'TokenList': aligned_tokens}
                        prel[elem] = projected
                    else:
                        prel[elem] = relation[elem]
                projected_relations.append(prel)
        
        return projected_relations


def main():
    
    inp = ['Die Aktienkurse sind seit letztem Monat gestiegen .'.split(), 'Obwohl die Wirtschaft allgemein rückläufig ist .'.split()]
    trans = ['Stock prices have risen since last month .'.split(), 'Although the economy is generally declining .'.split()] # would normally get this from translator
    pd = ProjanDisco()
    pd.annotate(inp, trans)


if __name__ == '__main__':
    main()