from simalign import SentenceAligner
from tqdm import tqdm
import requests

# This is where we want to insert Muhammed's align voting endpoint...
api_url = 'https://dcc9-134-96-105-142.ngrok-free.app/align'

"""
Class to align words, given source and target sentence. Currently only simalign (https://github.com/cisnlp/simalign) implemented, but will want to try out others here.
"""
class Aligner:
    
    def __init__(self):
        self.aligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")

    def align(self, src_sentence, trg_sentence):
        return self.aligner.get_word_aligns(src_sentence, trg_sentence)

    def align_sentences(self, src_sentences, trg_sentences):
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
        
def main():
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

if __name__ == '__main__':
    main()