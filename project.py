import translate
import align
import discoparse
import json

import time
from pprint import pprint



class ProjanDisco:
    def __init__(self, translator_name="deepl"):
        # self.translator = translate.Translator(translator_name=translator_name)
        self.translator = translate.AutoTranslator.get(translator_name=translator_name)
        self.aligner = align.Aligner()
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
        """Perform calling API and align 

        args:
          inp (list of list)
        """
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
        
        inp_tmp = [ " ".join(s) for s in trans]
        inp_tmp = trans
        discopy_result   = self.discopy.parse(inp_tmp)
        discopy_response = json.loads(discopy_result)
        print(f"num of inp, {len(inp)}")
        print(f"inp_tmp: {inp_tmp}")
        print(f"type(trans): {type(trans)}")
        print(f"type(discopy_result): {type(discopy_result)}")

        rel = discopy_response["relations"]
        pprint(f"orgin relations in response\n {rel}")
        print(f"num of response {len(rel)}")

        ###
        # testing
        ###
        # exm =  """{
        # "name": "John Doe",
        # "age": 30,
        # "city": "New York"
        # }"""
        # discopy_response = json.loads(exm)

        # Since translation is done sentence-by-sentence, number of sentences in srg and trg text should be the same
        assert len(inp) == len(trans)
        print("ProjanDisco", )
        alignments = self.aligner.align_sentences(inp, trans)
        id2token = {}
        tid = 0
        for sent in inp:
            print("sent in inp", sent)
            for token in sent:
                print("token in given sent", token)
                print("token id", token)
                id2token[tid] = token
                tid += 1
        print(f"inp: {inp}")
        print(f"trans: {trans}")

        pprint(f"discopy_response: {discopy_response}")
        print(f"alignments: {alignments}")
        print(f"id2token", id2token)
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
            print(f"len(relations): {relations}")

            for relation in relations:
                prel = {}
                for elem in relation:
                    print("elem", elem)
                    print("relation[ele]", relation[elem])
                    # ignoring CharacterSpanList altogether
                    if isinstance(relation[elem], dict) and 'TokenList' in relation[elem]:
                        print("relation[elem]",relation[elem])
                        print("relation[elem]['TokenList']", relation[elem]['TokenList'])
                        # TODO: suspect this might instead need to be the line below instead of what's currently active.
                        # aligned_tokens = [[a[1] for a in alignments if a[0] == t] for t in relation[elem]['TokenList']]
                        aligned_tokens = [[a[0] for a in alignments if a[1] == t] for t in relation[elem]['TokenList']]
                        
                        aligned_tokens = sorted(list(set([t for tl in aligned_tokens for t in tl])))
                        print("sorted aligned_tokens", aligned_tokens)
                        rawtext = ' '.join([id2token[i] for i in aligned_tokens]).strip()

                        # here: we got empty lists for these 
                        projected = {'RawText': rawtext, 'TokenList': aligned_tokens}
                        print("id2token", id2token)
                        print("rawtext", rawtext)
                        print("aligned_tokens",aligned_tokens)
                        # assert len(rawtext) != 0
                        # assert len(aligned_tokens) != 0
                        prel[elem] = projected
                    else:
                        prel[elem] = relation[elem]
                projected_relations.append(prel)
        print(f"projected_relations: {projected_relations}")
        return projected_relations




def main():
    
    inp = ['Die Aktienkurse sind seit letztem Monat gestiegen .'.split(), 'Obwohl die Wirtschaft allgemein rückläufig ist .'.split()]
    trans = ['Stock prices have risen since last month .'.split(), 'Although the economy is generally declining .'.split()] # would normally get this from translator
    pd = ProjanDisco()
    pd.annotate(inp, trans)


if __name__ == '__main__':
    main()
