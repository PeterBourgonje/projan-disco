import os
import re
import translate
import json
from tqdm import tqdm

"""
Using data from https://github.com/disrpt/sharedtask2023
"""

def conllu2sentences(conllu):

    sentences = {}
    lines = open(conllu).readlines()
    for i, line in enumerate(lines):
        line = line.strip()
        if re.search('^# text = ', line):
            sent = re.sub('^# text = ', '', line)
            sentences[re.sub('^# sent_id = ', '', lines[i-1]).strip()] = sent
    return sentences


def dump_translation(conllu, out):

    assert os.path.exists(conllu)
    sentences = conllu2sentences(conllu)
    translator = translate.Translator()
    outdict = {}
    targetlang = 'EN-US'
    for sid in tqdm(sentences, desc='Translating'):
        translation = translator.translate(sentences[sid], targetlang)
        outdict[sid] = {'src': sentences[sid], 'trg': translation}
    if not os.path.exists('translated'):
        os.mkdir('translated')
    outname = os.path.join('translated', out)
    json.dump(outdict, open(outname, 'w'), indent=2, ensure_ascii=False)
    

def parse_translations(translations):

    parsed = []
    # TODO: Break up input into texts to feed to discopy. Then re-figure out composing sentences to have reasonable word alignments (as those probably don't work well when feeding the entire src-trg text in one go).
 

def main():
	
    infile = r"..\sharedtask2023\data\por.pdtb.crpc\por.pdtb.crpc_test.conllu"
    outname = 'por.pdtb.crpc_test.pt-en.json'
    #dump_translation(infile, outname)
    translations = json.load(open(os.path.join('translated', outname)))
    parsed = parse_translations(translations)
    
    
    
	
if __name__ == '__main__':
	main()