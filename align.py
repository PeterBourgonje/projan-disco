from simalign import SentenceAligner
from transformers import AutoModel, AutoTokenizer
import itertools
import torch
from tqdm import tqdm
import requests
import sys


"""
Class to align words, given source and target sentence.
Currently implemented aligners:
- simalign (https://github.com/cisnlp/simalign)
- awesome (https://huggingface.co/aneuraz/awesome-align-with-co)

"""

SIM_ALIGN = 'simalign'
AWESOME = 'awesome'


class Aligner:
    
    def __init__(self, method):
        if method == SIM_ALIGN:
            self.alignment_method = SIM_ALIGN
            self.aligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")
        elif method == AWESOME:
            self.alignment_method = AWESOME
            self.model = AutoModel.from_pretrained("aneuraz/awesome-align-with-co")
            self.tokenizer = AutoTokenizer.from_pretrained("aneuraz/awesome-align-with-co")
            self.align_layer = 8
            self.threshold = 1e-3

        else:
            sys.stderr.write('ERROR: Method "%s" unknown.\n' % method)
            sys.exit()

    def align(self, src_sentence, trg_sentence):
        if self.alignment_method == SIM_ALIGN:
            return self.aligner.get_word_aligns(src_sentence, trg_sentence)

    def align_sentences(self, src_sentences, trg_sentences):

        if self.alignment_method == SIM_ALIGN:
            alignments = []
            tid_src = 0
            tid_trg = 0
            for src, trg in zip(src_sentences, trg_sentences):
                aligned = self.align(src, trg)['mwmf']
                re_aligned = [(x[0]+tid_src, x[1]+tid_trg) for x in aligned]
                tid_src += len(src)
                tid_trg += len(trg)
                alignments.extend(re_aligned)
            return alignments
        elif self.alignment_method == AWESOME:
            alignments = []
            tid_src = 0
            tid_trg = 0
            for src, trg in zip(src_sentences, trg_sentences):
                token_src = [self.tokenizer.tokenize(word) for word in src]
                token_trg = [self.tokenizer.tokenize(word) for word in trg]
                wid_src = [self.tokenizer.convert_tokens_to_ids(x) for x in token_src]
                wid_trg = [self.tokenizer.convert_tokens_to_ids(x) for x in token_trg]
                ids_src = self.tokenizer.prepare_for_model(list(itertools.chain(*wid_src)), return_tensors='pt',
                                                               model_max_length=self.tokenizer.model_max_length,
                                                               truncation=True)['input_ids']
                ids_trg = self.tokenizer.prepare_for_model(list(itertools.chain(*wid_trg)), return_tensors='pt',
                                                               model_max_length=self.tokenizer.model_max_length,
                                                               truncation=True)['input_ids']
                sub2word_map_src = []
                for i, word_list in enumerate(token_src):
                    sub2word_map_src += [i for x in word_list]
                sub2word_map_trg = []
                for i, word_list in enumerate(token_trg):
                    sub2word_map_trg += [i for x in word_list]

                self.model.eval()
                with torch.no_grad():
                    out_src = self.model(ids_src.unsqueeze(0), output_hidden_states=True)[2][self.align_layer][0, 1:-1]
                    out_tgt = self.model(ids_trg.unsqueeze(0), output_hidden_states=True)[2][self.align_layer][0, 1:-1]

                    dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

                    softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
                    softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

                    softmax_inter = (softmax_srctgt > self.threshold) * (softmax_tgtsrc > self.threshold)

                align_subwords = torch.nonzero(softmax_inter, as_tuple=False)
                align_words = set()
                for i, j in align_subwords:
                    align_words.add((sub2word_map_src[i], sub2word_map_trg[j]))
                re_aligned = [(x[0] + tid_src, x[1] + tid_trg) for x in align_words]
                tid_src += len(src)
                tid_trg += len(trg)
                alignments.extend(re_aligned)
            return sorted(alignments, key=lambda x: x[0])


def main():

    src = ['Because John finished his homework early , he decided to play video games .'.split()]
    trg = ['Weil John seine Hausaufgaben früher beendet hatte , beschloss er , Videospiele zu spielen .'.split()]
    al = Aligner('simalign')
    alignments = al.align_sentences(src, trg)
    print(alignments)
    al = Aligner('awesome')
    alignments = al.align_sentences(src, trg)
    print(alignments)
    """
    src_sentence = 'Because John finished his homework early , he decided to play video games .'.split()
    trg_sentence = 'Weil John seine Hausaufgaben früher beendet hatte , beschloss er , Videospiele zu spielen .'.split()
    al = Aligner()
    alignments = al.align(src_sentence, trg_sentence)
    print(alignments)

    src_sentence = "This is a test ."
    trg_sentence = "Das ist ein Test ."
    data = {
        "src_sentence": src_sentence,
        "trg_sentence": trg_sentence
    }
    response = requests.post(api_url, json=data)
    if response.status_code == 200:
        result = response.json()
        mwmf_alignments = result.get('mwmf_alignments')
        print("MWMF Alignments:", mwmf_alignments)
    else:
        print("Error:", response.text)
    """

if __name__ == '__main__':
    main()