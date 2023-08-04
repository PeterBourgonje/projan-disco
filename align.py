from simalign import SentenceAligner

"""
Class to align words, given source and target sentence. Currently only simalign (https://github.com/cisnlp/simalign) implemented, but will want to try out others here.
"""
class Aligner:
    
    def __init__(self):
        self.aligner = SentenceAligner(model="bert", token_type="bpe", matching_methods="mai")
    
    def align(self, src_sentence, trg_sentence):
        return self.aligner.get_word_aligns(src_sentence, trg_sentence)
        
        
def main():
    src_sentence = 'Because John finished his homework early , he decided to play video games .'.split()
    trg_sentence = 'Weil John seine Hausaufgaben früher beendet hatte , beschloss er , Videospiele zu spielen .'.split()
    al = Aligner()
    alignments = al.align(src_sentence, trg_sentence)
    print(alignments)
        
if __name__ == '__main__':
    main()