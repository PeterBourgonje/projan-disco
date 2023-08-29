import os
import re
import translate
import json
from tqdm import tqdm
import project

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


def get_texts_from_sentences(transdict):

    texts = {}
    src_text, trg_text = [], []
    dictlen = len(transdict.keys())
    for i, sid in enumerate(transdict.keys()):
        sid_int = int(re.match('.*-(\d+)', sid).groups()[0])
        doc_id = re.match('(.*)-\d+', sid).groups()[0]
        if i > 0:
            prev_sid_int = int(re.match('.*-(\d+)', list(transdict.keys())[i-1]).groups()[0])
            if prev_sid_int > sid_int:
                prev_doc_id = re.match('(.*)-\d+', list(transdict.keys())[i-1]).groups()[0]
                texts[prev_doc_id] = (src_text, trg_text)
                src_text = [transdict[sid]['src']]
                trg_text = [transdict[sid]['trg']]
            else:
                src_text.append(transdict[sid]['src'])
                trg_text.append(transdict[sid]['trg'])
        else:
            src_text = [transdict[sid]['src']]
            trg_text = [transdict[sid]['trg']]
    texts[doc_id] = (src_text, trg_text)
    
    return texts    


def parse_translations(translations):

    parsed = {}
    texts = get_texts_from_sentences(translations)
    pd = project.ProjanDisco()
    for doc_id in tqdm(texts, desc="Processing docs"):
        src_sents, trg_sents = texts[doc_id]
        src_sents = [s.split() for s in src_sents]
        trg_sents = [s.split() for s in trg_sents]
        relations = pd.annotate(src_sents, trg_sents)
        parsed[doc_id] = relations

    return parsed


def parsed2conllu(infile, parsed):

    docid2connectives = {}
    docid2condebug = {}
    for docid in parsed:
        connectives = {}
        condebug = {}
        for rel in parsed[docid]:
            if rel['Type'] == 'Explicit':
                ckey = rel['Connective']['TokenList'][0]
                connectives[ckey] = rel['Connective']['TokenList']
                condebug[ckey] = rel['Connective']['RawText'].split()[0]
        docid2connectives[docid] = connectives
        docid2condebug[docid] = condebug

    outfile = open(os.path.splitext(infile)[0] + '_discopyrojected.conllu', 'w')
    lines = open(infile).readlines()
    lines = [re.sub('Seg=[BI]-Conn', '_', x) for x in lines]  # strip all existing annotations
    curdict = None
    curdebdict = None
    tc = 0
    for i, line in enumerate(lines):
        if re.search(r'^# newdoc_id = ', line):
            docid = re.sub(r'^# newdoc_id = ', '', line).strip()
            if docid in docid2connectives:
                curdict = docid2connectives[docid]
                curdebdict = docid2condebug[docid]
                tc = 0
            else:
                break
        if re.search(r'^\d+\t', line):
            if tc in curdict:
                assert line.split('\t')[1] == curdebdict[tc]
                lines[i] = '\t'.join(lines[i].split('\t')[:-1] + ['Seg=B-Conn\n'])
                if len(curdict[tc]) > 1:
                    for j, nt in enumerate(curdict[tc][1:]):
                        # TODO: test if the line below works alright!
                        lines[i+j+1] = '\t'.join(lines[i+j+1].split('\t')[:-1] + ['Seg=I-Conn\n'])
            tc += 1
    for line in lines:
        outfile.write(line)
    outfile.close()
    

def main():

    infile = r"..\sharedtask2023\data\por.pdtb.crpc\por.pdtb.crpc_test.conllu"
    outname = 'por.pdtb.crpc_test.pt-en.json'
    #dump_translation(infile, outname)
    translations = json.load(open(os.path.join('translated', outname)))
    parsed = parse_translations(translations)
    parsed2conllu(infile, parsed)
    

if __name__ == '__main__':
    main()