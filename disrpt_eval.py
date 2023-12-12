import os
import re
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


def dump_translation(conllu, out, dump_translation_dir, args):
    """Return json dumped transaltion. """
    assert os.path.exists(conllu)
    
    # instanize class
    corpus = conllu.split("/")[-1].split("_")[0]
    corpus_processor = AutoTask.get(corpus)
    sentences = corpus_processor.get_conllu2sentences(conllu)

    #translator = translate.Translator()
    translator = translate.AutoTranslator.get(translator_name=args.translator_api)
    outdict = {}
    targetlang = 'EN-US' if args.translator_api == 'deepl' else 'en'
    for sid in tqdm(sentences, desc='Translating'):
        # check we're passing sentence in correct way 
        ### test block ###
        # print(f"src sentence: {sentences[sid]}")
        # outdict[sid] = {'src': "1 2 3", 'trg': "a b c"}
        ### test block ###
        print("inp",sentences[sid])
        # Calling translator
        translation = translator.translate(sentences[sid], targetlang) # 
        # translation = "translated: " + sentences[sid]
        
        outdict[sid] = {'src': sentences[sid], 'trg': translation}
    
    if not os.path.exists(dump_translation_dir):
        os.mkdir(dump_translation_dir)
    outname = os.path.join(dump_translation_dir, out)

    dumped_translation = json.dump(outdict, open(outname, 'w'), indent=2, ensure_ascii=False)
    print(f"dumping translation to : {outname}")
    return dumped_translation


def get_texts_from_sentences(transdict, doc_id_pattern, sent_id_pattern):
    """Convert transdict (dict) to texts (dict).
    
    """
    texts = {}
    src_text, trg_text = [], []
    dictlen = len(transdict.keys())
    print(f"dictlen all keys", transdict.keys())
    print(f"dictlen", dictlen)
    for i, sid in enumerate(transdict.keys()):
        sid_int = int(re.match(sent_id_pattern, sid).groups()[0])
        doc_id = re.match(doc_id_pattern, sid).groups()[0]

        print("doc_id", doc_id)
        print("sid_int",sid_int)
        if i > 0:
            prev_sid_int = int(re.match(sent_id_pattern, list(transdict.keys())[i-1]).groups()[0])
            print("prev_sid_int",prev_sid_int)
            print("sid_int", sid_int)
            if prev_sid_int >= sid_int:
                prev_doc_id = re.match(doc_id_pattern, list(transdict.keys())[i-1]).groups()[0]
                print("prev_doc_id", prev_doc_id)
                print("yes prev_sid_int > sid_int")
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
    
    print("src", len(src_text), "tgt", len(trg_text))
    print("texts.keys()",texts.keys())
    for k,v in texts.items():
        print("key", k)
        for idx, sent in enumerate(texts[k]):
            print(f"id: {idx}\nsentences", sent[0])
    # value is doc_id
    total_sents = [len(v[0]) for _,v in texts.items()] # ensure all examples 
    print(total_sents)
    print([len(v[1]) for _,v in texts.items()])
    print("texts.keys()",texts.keys())
    
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

    print("selecting 2 examples")
    print(f"texts (disrpt_eval): {texts}") # dict
    print(f"type(texts): {type(texts)}")
    print(f"texts.keys(): {texts.keys()}")
    
    def preprocess(sent):
        return sent.replace(".", " .").replace(",", " ,")
    pd = project.ProjanDisco(args.translator_api)
    
    print("texts.keys()", texts.keys())
    
    for doc_id in tqdm(texts, desc="Processing docs"):
        src_sents_, trg_sents = texts[doc_id]
        src_sents = [s.split() for s in src_sents_]
        trg_sents  =  [s.split() for s in trg_sents]

        # get list according doc id
        src_sents = src_only_texts[doc_id]
        assert len(src_sents) == len(src_sents) == len(trg_sents)
        
        # src_sents, trg_sents = texts[doc_id]["src"], texts[doc_id]["trg"] # nested dict
        # list of sequence of tokens , (batch_size, seq_len)
        # `seq_len` is example-dependent integer
        # src_sents = [src_sents.split()] 
        # trg_sents = [trg_sents.split()]
        
        # print("src_sents", src_sents[:2])
        # print("trg_sents", trg_sents[:2])     
        relations = pd.annotate(src_sents, trg_sents)
        # print(f"src_sents (disrpt_eval): {src_sents}")
        # print(f"trg_sents (disrpt_eval): {trg_sents}")
        # print(f"relations (disrpt_eval): {relations}")
        
        parsed[doc_id] = relations
    pprint(f"parsed: {parsed}")
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
    print("key in parsed", parsed.keys())
    for docid in parsed:
        connectives = {}
        condebug = {}
        for rel in parsed[docid]:
            print("each rel", rel)
            if rel['Type'] == 'Explicit':
                print("rel['Type'] == 'Explicit' !!!")
                print("rel['Connective']")

                if len(rel['Connective']['TokenList']) == 0:
                    pass
                else:
                    ckey = rel['Connective']['TokenList'][0]
                    connectives[ckey] = rel['Connective']['TokenList']
                    condebug[ckey] = rel['Connective']['RawText'].split()[0]
        docid2connectives[docid] = connectives
        docid2condebug[docid] = condebug
    
    print("docid2connectives", docid2connectives)
    print("docid2condebug", docid2condebug)
    # output as conllu
    outfile_path = os.path.splitext(infile)[0] + '_discopyrojected.conllu'
    outfile_path = args.pred_output_dir + "/" + outfile_path.split("/")[-1]
    print("outfile_path",outfile_path)
    outfile = open(outfile_path, 'w')
    lines = open(infile).readlines()
    lines = [re.sub('Seg=[BI]-Conn', '_', x) for x in lines]  # strip all existing annotations
    curdict = None
    curdebdict = None
    tc = 0
    print("lines[:20]", lines[:20])
    for i, line in enumerate(lines):
        corpus = args.infile.split("/")[-1].split("_")[0]
        doc_id_prefix = Corpus2DocIdPrefix[corpus]
        # Assign token an index if new document
        if re.search(doc_id_prefix, line):
            docid = re.sub(doc_id_prefix, '', line).strip()
            print("find new docid",docid)
            if docid in docid2connectives:
                curdict = docid2connectives[docid]
                curdebdict = docid2condebug[docid]
                tc = 0
            # this force docid has to be in `docid2connectives`, otherwise stop program
            else:
                pass

        print(f"line id: {i}, line: {line}")
        print("token cnt (id)", tc)
        print("curdict", curdict)
        print("curdebdict", curdebdict)
        if re.search(r'^\d+\t', line):
            if tc in curdict:
                print("line.split(\t)[1]", line.split('\t')[1])
                print("curdebdict[tc]", curdebdict[tc])
                print(tc)
                # assert line.split('\t')[1] == curdebdict[tc]
                print("curdebdict[tc]", curdebdict[tc])
                line_with_label = '\t'.join(lines[i].split('\t')[:-1] + ['Seg=B-Conn\n'])
                print("line_with_label",line_with_label)
                lines[i] = line_with_label
                if len(curdict[tc]) > 1:
                    for j, nt in enumerate(curdict[tc][1:]):
                        lines[i+j+1] = '\t'.join(lines[i+j+1].split('\t')[:-1] + ['Seg=I-Conn\n'])
            tok = line.split('\t')[1]
            print(f"tc: {tc}, token: {tok}")
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
    # dump_translation(infile, outname, dump_translation_dir, args)
    translations = json.load(open(os.path.join(args.dump_translation_dir, outname)))
    
    print("translations", translations)
    print("type(translations)", type(translations))
    
    parsed = parse_translations(translations, src_only_texts, doc_id_pattern, sent_id_pattern, args)
    parsed = json.load(open(os.path.join(args.dump_parser_dir, outname)))
    print("parsed", parsed)
    print("type(parsed)", type(parsed))
    
    parsed2conllu(infile, parsed, args)
    

if __name__ == '__main__':
    main()
