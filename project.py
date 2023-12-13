import translate
import align
import discoparse
import json
import spacy


class ProjanDisco:

    def __init__(self):
        self.translator = translate.Translator()
        #self.aligner = align.Aligner('simalign')
        self.aligner = align.Aligner('awesome')
        self.discopy = discoparse.Discopy()

    def merge_batches(self, batches):
        response = {'docID': batches[-1]['docID'], 'meta': batches[-1]['meta'],
                    'text': '\n'.join(b['text'] for b in batches), 'sentences': [], 'relations': []}
        sentences = []
        relations = []
        c_offset = 0
        t_offset = 0
        for batch in batches:
            for s in batch['sentences']:
                # the CharacterOffsets are not really informative (and not used for alignment) in this /tokens endpoint,
                # but implementing batch-wise increment here in case they are corrected in some future version.
                s['tokens'] = [{'surface': t['surface'], 'characterOffsetBegin': t['characterOffsetBegin']+c_offset,
                                'characterOffsetEnd': t['characterOffsetEnd']+c_offset, 'upos': t['upos'],
                                'xpos': t['xpos'], 'lemma': t['lemma']} for t in s['tokens']]
                sentences.append(s)
            for r in batch['relations']:
                r['Arg1']['CharacterSpanList'] = [[c+c_offset for spanlist in r['Arg1']['CharacterSpanList'] for c in spanlist]]
                r['Arg1']['TokenList'] = [t + t_offset for t in r['Arg1']['TokenList']]
                r['Arg2']['CharacterSpanList'] = [[c+c_offset for spanlist in r['Arg2']['CharacterSpanList'] for c in spanlist]]
                r['Arg2']['TokenList'] = [t + t_offset for t in r['Arg2']['TokenList']]
                r['Connective']['CharacterSpanList'] = [[c+c_offset for spanlist in r['Connective']['CharacterSpanList'] for c in spanlist]]
                r['Connective']['TokenList'] = [t + t_offset for t in r['Connective']['TokenList']]
                relations.append(r)
            c_offset += batch['sentences'][-1]['tokens'][-1]['characterOffsetEnd'] + 1  # joining on newline, so adding one more...
            t_offset += sum(len(s['tokens']) for s in batch['sentences'])
        response['sentences'] = sentences
        response['relations'] = relations
        return response

    def annotate(self, inp, trans):

        # checking that input is pre-sentencized and pre-tokenized
        assert isinstance(inp, list)
        assert isinstance(trans, list)
        assert all(isinstance(x, list) for x in inp)
        assert all(isinstance(x, list) for x in trans)
        # Code below is to parse batch-wise (pretty rudimentary though, not cascaded), but didn't solve my memory issue. 
        # Perhaps token-based (some individual sentence being too long for bert?) 
        #batch_size = 1000
        #prev_index = 0
        #parsed_batches = []
        #for batch_index in range(batch_size, len(trans), batch_size):
            #batch = trans[prev_index:batch_index]
            #parsed_batches.append(json.loads(self.discopy.parse(batch)))
            #prev_index = batch_index
        #final_batch = trans[prev_index:len(trans)]
        #parsed_batches.append(json.loads(self.discopy.parse(final_batch)))
        #discopy_response = self.merge_batches(parsed_batches)
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
                        # TODO: suspect this might instead need to be the line below instead of what's currently active.
                        # aligned_tokens = [[a[1] for a in alignments if a[0] == t] for t in relation[elem]['TokenList']]
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

    """
    inp = ['Die Aktienkurse sind seit letztem Monat gestiegen .'.split(), 'Obwohl die Wirtschaft allgemein rückläufig ist .'.split()]
    trans = ['Stock prices have risen since last month .'.split(), 'Although the economy is generally declining .'.split()] # would normally get this from translator
    pd = ProjanDisco()
    projected = pd.annotate(inp, trans)
    print(projected)
    """
    nlp_de = spacy.load('de_core_news_sm')
    trans = translate.Translator()

    input_text = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'

    src_sentences = [[t.text for t in s] for s in nlp_de(input_text).sents]
    trg_sentences = [trans.translate(' '.join(s), 'EN-US').split() for s in src_sentences]
    pd = ProjanDisco()
    projected = pd.annotate(src_sentences, trg_sentences)
    print(projected)


if __name__ == '__main__':
    main()