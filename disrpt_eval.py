import os
import re
import sys
import translate
import json
import argparse
from tqdm import tqdm
import project

import conllu as conllu_pkg
from pprint import pprint 
from tasks import AutoTask
"""
Using data from https://github.com/disrpt/sharedtask2023
"""

Corpus2DocIdPattern = {
    "ita.pdtb.luna": '(.*-\d+)-\d+',
    "por.pdtb.crpc": '(.*)-\d+',
    "por.pdtb.tedm": '(.*)-\d+',
    "tha.pdtb.tdtb": '(.*)-\d+',
    "tur.pdtb.tdb": '(.*)-\d+',
    "tur.pdtb.tedm": '(.*)-\d+',
    "zho.pdtb.cdtb": '(.*)-\d+',
}


Corpus2SentIdPattern = {
    "ita.pdtb.luna": '.*-\d+-(\d+)',
    "por.pdtb.crpc": '.*-(\d+)',
    "por.pdtb.tedm": '.*-(\d+)',
    "tha.pdtb.tdtb": '.*-(\d+)',
    "tur.pdtb.tdb":  '.*-(\d+)',
    "tur.pdtb.tedm": '.*-(\d+)',
    "zho.pdtb.cdtb": '.*-(\d+)', # this is only work when we add sent_id to translation file
}


Corpus2DocIdPrefix = {
    "ita.pdtb.luna": r'^# newturn_id = ',
    "por.pdtb.crpc": r'^# newdoc_id = ',
    "por.pdtb.tedm": r'^# newdoc_id = ',
    "tha.pdtb.tdtb": r'^# newdoc_id = ',
    "tur.pdtb.tdb":  r'^# newdoc id = ',
    "tur.pdtb.tedm": r'^# newdoc_id = ',
    "zho.pdtb.cdtb": r'^# newdoc id = '
}


CORPORA = {
    "ita.pdtb.luna",
    "por.pdtb.crpc",
    "por.pdtb.tedm",
    "tha.pdtb.tdtb",
    "tur.pdtb.tdb",
    "tur.pdtb.tedm",
    "zho.pdtb.cdtb"
}

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



def dump_translation(conllu, out, dump_translation_dir, args):
    """Return json dumped transaltion. """
    assert os.path.exists(conllu)
    
    # instanize class
    corpus = conllu.split("/")[-1].split("_")[0]
    corpus_processor = AutoTask.get(corpus)
    sentences = corpus_processor.get_conllu2sentences(conllu)

    #translator = translate.Translator()
    translator = translate.AutoTranslator.get(translator_name=args.translator_api)

    # sentences = None
    # if format == 'marked':
    #     sentences = conllu2sentences(conllu)
    # elif format == 'somewhat_marked':
    #     sentences = conllu2sentences_somewhatmarked(conllu)
    # elif format == 'non_marked':
    #     sentences = conll2sentences_nonmarked(conllu)
    # else:
    #     sys.stderr.write('ERROR: Format "%s" unknown.\n' % format)
    #     sys.exit()
    # translator = translate.Translator()

    outdict = {}
    targetlang = 'EN-US' if args.translator_api == 'deepl' else 'en'
    for sid in tqdm(sentences, desc='Translating'):
        # Calling translator
        translation = translator.translate(sentences[sid], targetlang) # 
        # translation = "translated: " + sentences[sid]
        outdict[sid] = {'src': sentences[sid], 'trg': translation}
    
    if not os.path.exists(dump_translation_dir):
        os.mkdir(dump_translation_dir)
    outname = os.path.join(dump_translation_dir, out)

    dumped_translation = json.dump(outdict, open(outname, 'w'), indent=2, ensure_ascii=False)
    return dumped_translation


def get_texts_from_sentences(transdict, doc_id_pattern, sent_id_pattern):
    """Convert transdict (dict) to texts (dict).
    
    """
    texts = {}
    src_text, trg_text = [], []
    dictlen = len(transdict.keys())
    for i, sid in enumerate(transdict.keys()):
        sid_int = int(re.match(sent_id_pattern, sid).groups()[0])
        doc_id = re.match(doc_id_pattern, sid).groups()[0]

        if i > 0:
            prev_sid_int = int(re.match(sent_id_pattern, list(transdict.keys())[i-1]).groups()[0])
            if prev_sid_int >= sid_int:
                prev_doc_id = re.match(doc_id_pattern, list(transdict.keys())[i-1]).groups()[0]

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
    

    # value is doc_id
    total_sents = [len(v[0]) for _,v in texts.items()] # ensure all examples 
    assert sum(total_sents) == dictlen
    return texts    


def parse_translations(translations, src_only_texts, doc_id_pattern, sent_id_pattern, args):
    """

    Args:
     translations
     src_only_texts: dict. Using document id as key

    Returns:
      parsed (dict): key is document id 

    """
    parsed = {}
    texts = get_texts_from_sentences(translations, doc_id_pattern, sent_id_pattern)
    pd = project.ProjanDisco(args.aligner_api , args.translator_api)
    for doc_id in tqdm(texts, desc="Processing docs"):
        src_sents_, trg_sents = texts[doc_id]
        src_sents = [s.split() for s in src_sents_]
        trg_sents  =  [s.split() for s in trg_sents]

        # get list according doc id
        src_sents = src_only_texts[doc_id]
        assert len(src_sents) == len(src_sents) == len(trg_sents)
        
        relations = pd.annotate(src_sents, trg_sents)
        parsed[doc_id] = relations
    dump_parser_dir = args.dump_parser_dir
    if not os.path.exists(dump_parser_dir):
        os.mkdir(dump_parser_dir)
    outname = os.path.join(dump_parser_dir, args.outname)

    dumped_parsed = json.dump(parsed, open(outname, 'w'), indent=2, ensure_ascii=False)
    print(f"dumping translation to : {outname}")
    return parsed


def parsed2conllu(infile, parsed, args):

    docid2connectives = {}
    docid2condebug = {}
    for docid in parsed:
        connectives = {}
        condebug = {}
        for rel in parsed[docid]:
            if rel['Type'] == 'Explicit':

                if len(rel['Connective']['TokenList']) == 0:
                    pass
                else:
                    ckey = rel['Connective']['TokenList'][0]
                    connectives[ckey] = rel['Connective']['TokenList']
                    condebug[ckey] = rel['Connective']['RawText'].split()[0]
        docid2connectives[docid] = connectives
        docid2condebug[docid] = condebug
    
    # output as conllu
    outfile_path = os.path.splitext(infile)[0] + '_discopyrojected.conllu'
    outfile_path = args.pred_output_dir + "/" + outfile_path.split("/")[-1]

    outfile = open(outfile_path, 'w')
    lines = open(infile).readlines()
    lines = [re.sub('Seg=[BI]-Conn', '_', x) for x in lines]  # strip all existing annotations
    curdict = None
    curdebdict = None
    tc = 0
    for i, line in enumerate(lines):
        corpus = args.infile.split("/")[-1].split("_")[0]
        doc_id_prefix = Corpus2DocIdPrefix[corpus]
        # Assign token an index if new document
        if re.search(doc_id_prefix, line):
            docid = re.sub(doc_id_prefix, '', line).strip()
            if docid in docid2connectives:
                curdict = docid2connectives[docid]
                curdebdict = docid2condebug[docid]
                tc = 0
            # this force docid has to be in `docid2connectives`, otherwise stop program
            else:
                pass

        if re.search(r'^\d+\t', line):
            if tc in curdict:
                assert line.split('\t')[1] == curdebdict[tc]
                line_with_label = '\t'.join(lines[i].split('\t')[:-1] + ['Seg=B-Conn\n'])
                lines[i] = line_with_label
                if len(curdict[tc]) > 1:
                    for j, nt in enumerate(curdict[tc][1:]):
                        lines[i+j+1] = '\t'.join(lines[i+j+1].split('\t')[:-1] + ['Seg=I-Conn\n'])
            tok = line.split('\t')[1]
            tc += 1

    for line in lines:
        outfile.write(line)
    outfile.close()
    print(f"Saving file to: {outfile_path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--infile", type=str, default=r"../sharedtask2023/data/por.pdtb.crpc/por.pdtb.crpc_test.conllu")
    p.add_argument("--outname", type=str, default='por.pdtb.crpc_test.pt-en.json')
    p.add_argument("--dump_translation_dir", type=str, default='translated')
    p.add_argument("--dump_parser_dir", type=str, default='parsed')
    p.add_argument("--aligner_api", type=str, default='simalign')
    p.add_argument("--translator_api", type=str, default='deepl')
    p.add_argument("--pred_output_dir", type=str, default='')
    args = p.parse_args()

    # get the regular expression pattern to get doc/sent id
    corpus = args.infile.split("/")[-1].split("_")[0]
    
    sent_id_pattern = Corpus2SentIdPattern[corpus]
    doc_id_pattern = Corpus2DocIdPattern[corpus]
    
    # instanize class
    corpus_processor = AutoTask.get(corpus)
    # This is done for potentially better alignment by using pre-tokenized tokens (token in each line)
    # dict: doc_id as key -> list of tokens sentences 
    src_only_texts = corpus_processor.get_conllu2tokensentences(args.infile, doc_id_pattern)
    
    infile = args.infile
    outname = args.outname
    dump_translation_dir = args.dump_translation_dir

    # test dump file
    dump_translation(infile, outname, dump_translation_dir, args)
    translations = json.load(open(os.path.join(args.dump_translation_dir, outname)))
    
    parsed = parse_translations(translations, src_only_texts, doc_id_pattern, sent_id_pattern, args)
    parsed = json.load(open(os.path.join(args.dump_parser_dir, outname)))
    
    parsed2conllu(infile, parsed, args)

    

if __name__ == '__main__':
    main()
