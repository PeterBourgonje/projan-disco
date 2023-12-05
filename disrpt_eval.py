import os
import re
import sys
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


def conll2sentences_nonmarked(conllu):
    sentences = {}
    lines = open(conllu, encoding='utf8').readlines()
    """
    Use this fuction if sentences are not marked at all (i.e. newline is the only clue) on the conllu format, like so:
    18	网络	网络	NN	NN	_	19	nn	_	_
    19	招生	招生	NN	NN	_	17	pobj	_	_

    1	新华社	新华社	NR	NR	_	7	dep	_	_
    2	福州	福州	NR	NR	_	7	dep	_	_
    3	十二月	十二月	NT	NT	_	7	dep	_	_
    """
    sent = []
    _id = 0
    for i, line in enumerate(lines):
        if re.match(r'^\s+', line):
            sentences[_id] = ' '.join(sent)
            sent = []
            _id += 1
        elif re.search(r'^\d+\t', line):
            t = line.split('\t')[1]
            sent.append(t)

    return sentences


def conllu2sentences_somewhatmarked(conllu):

    sentences = {}
    lines = open(conllu, encoding='utf8').readlines()
    """
    Use this fuction if sentences are not explicitly marked in the conllu format, like so:
    # newutterance_id = 0705000001-3-2
    1	dicevamo	dire	VERB	V	Mood=Ind|Number=Plur|Person=1|Tense=Pres|VerbForm=Fin	7	conj	7:conj	_
    2	che	che	SCONJ	CS	_	12	mark	12:mark	_
    3	hai	avere	VERB	V	Mood=Ind|Number=Sing|Person=2|Tense=Pres|VerbForm=Fin	10	ccomp	10:ccomp	_
    4	problemi	problema	NOUN	S	Gender=Masc|Number=Plur	12	obj	12:obj	_
    5	di	di	ADP	E	_	15	mark	15:mark	_
    """
    sent = []
    _id = ''
    for i, line in enumerate(lines):
        if re.search(r'^# newutterance_id', line):
            sentences[_id] = ' '.join(sent)
            sent = []
            _id = re.sub(r'^# newutterance_id = ', '', line).strip()
        elif re.search(r'^\d+\t', line):
            t = line.split('\t')[1]
            sent.append(t)

    return sentences


def dump_translation(conllu, out, format):

    assert os.path.exists(conllu)
    sentences = None
    if format == 'marked':
        sentences = conllu2sentences(conllu)
    elif format == 'somewhat_marked':
        sentences = conllu2sentences_somewhatmarked(conllu)
    elif format == 'non_marked':
        sentences = conll2sentences_nonmarked(conllu)
    else:
        sys.stderr.write('ERROR: Format "%s" unknown.\n' % format)
        sys.exit()
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
                        lines[i+j+1] = '\t'.join(lines[i+j+1].split('\t')[:-1] + ['Seg=I-Conn\n'])
            tc += 1
    for line in lines:
        outfile.write(line)
    outfile.close()
    

def main():

    #infile = r"..\sharedtask2023\data\por.pdtb.crpc\por.pdtb.crpc_test.conllu"
    #outname = 'por.pdtb.crpc_test.pt-en.json'
    #dump_translation(infile, outname, 'marked')
    #infile = r"C:\Users\bourg\Desktop\various\disco-stringmatcher\projan_experiments\data\zho.pdtb.cdtb_test.conllu"
    #outname = 'zho.pdtb.cdtb_test.zh-en.json'
    #dump_translation(infile, outname, 'non_marked')

    infile = r"..\sharedtask2023\data\ita.pdtb.luna\ita.pdtb.luna_test.conllu"
    outname = 'ita.pdtb.luna_test.zh-en.json'
    dump_translation(infile, outname, 'somewhat_marked')

    #translations = json.load(open(os.path.join('translated', outname)))
    #parsed = parse_translations(translations)
    #parsed2conllu(infile, parsed)
    

if __name__ == '__main__':
    main()