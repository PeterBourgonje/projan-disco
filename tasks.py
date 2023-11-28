"""Define the class for processing CoNLL-U Schema Corpus

`AbstractTask` defines the corpus processor for general usage.
Each PDTB-style corpus inhereit this parent class. (we assume test split.)
There are three main methods for the processor: 
    
    (1) conllu_to_parsed_sentences: 

        The is designed as we found a blend word is separated into two topken and appeared in gold file.

        
        because `ita.pdtb.luna` and `zho.pdtb.cdtb` do not have text head.

        Note. This might be not being used anymore.
        As it seems 

    (2) get_conllu2tokensentences
    
    (3) get_conllu2sentences 

""" 
from collections import OrderedDict
import collections 
import abc
import functools
from typing import Callable, List, Mapping
import logging
import numpy as np
import re
import conllu as conllu_pkg

logger = logging.getLogger(__name__)

class AbstractTask(abc.ABC):
    doc_id_prefix = "newdoc_id"
    sent_id_prefix = "sent_id"

    def __init__(self):
        pass
    

    def _remove_line_start_with_two_token(sentences):
        """
          sentences: List of sentences (str)
        """
        # Remove the line started with `7-8 arasındaki ...` ""
        matches = list()
        for l in lines:
            if re.search(r"\d+-\d+", l):
                pass
            else:
                matches.append(l)
        return matches

    # Use parse() to parse into a list of sentences
    def conllu_to_parsed_sentences(self, conllu):
        # remove the line with adjacent tokens
        lines = open(conllu).readlines()

        # This might make string can be parsed property.
        # matches = "\n".join([ l for l in lines if re.search(r"\d+-\d+") != True])
    
        matches = _remove_line_start_with_two_token(lines)
        matches = "".join(matches)
         
        # matches = re.sub(r"\n(\d+-\d+\t.*)\n", "", lines)
        print("matches[:50000]", matches[:10000])
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]

            assert doc_id != None
        return sents

    def get_conllu2tokensentences(self, conllu, doc_id_pattern):
        """Return dict obj
          
        Each sentence is tokens of 

        Returns:
          doc_id -> (list of sentence)
        """
        texts = {}
        sentences = {}
        src_sents = list()

        sents = self.conllu_to_parsed_sentences(conllu)
        # get the list of tokens for each examples
        for sent in sents:

            sent_id = sent.metadata["sent_id"]
            doc_id = re.match(doc_id_pattern, sent_id).groups()[0]
            print("doc_id", doc_id)
            print("sent", sent)
            # {'id': 1, 'form': 'Teşekkür', 'lemma': 'teşekkür', 'upos': 'NOUN', 'xpos': 'Noun', 'feats': {'Case': 'Nom', 'Number': 'Sing', 'Person': '3'}, 'head': 0, 'deprel': 'root', 'deps': [('root', 0)], 'misc': None}
            tokens  = [obj["form"] for obj in sent]
            tok_ids = [obj["id"]   for obj in sent]
            
            if doc_id not in texts:
                texts[doc_id] = [tokens]
            else:
                texts[doc_id].append(tokens)
            # Trapezoidal rule
            idx_sum = (tok_ids[0]+tok_ids[-1])*(tok_ids[-1])/2
            # assert sum(tok_ids) == idx_sum
        return texts

    def get_conllu2sentences(self, conllu):
        """Return the `sentences`. 

        """
        # sentences = {}
        # lines = open(conllu).readlines()
        # for i, line in enumerate(lines):
        #     line = line.strip()
        #     if re.search('^# text = ', line):
        #         sent = re.sub('^# text = ', '', line)
        #         sentences[re.sub('^# sent_id = ', '', lines[i-1]).strip()] = sent
        # return sentences

        lines = open(conllu).readlines()

        matches = _remove_line_start_with_two_token(lines)
        matches = "".join(matches)
        
        matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            assert doc_id != None

        sentences = {}
        for sent in sents:
            # sent_id
            metadata =  sent.metadata
            sent_id = metadata[self.sent_id_prefix]  
            # text = sent.metadata["text"] # get text from text head
            text = " ".join([obj["form"] for obj in sent])
            sentences[sent_id] = text
            
        return sentences


class ItaTdtbLunaProcessor(AbstractTask):
    sent_id_prefix = "newutterance"
    
    def conllu_to_parsed_sentences(self, conllu):
        lines = open(conllu).read()    
        matches = re.sub(r"\n(\d+-\d+\t.*)\n", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            # create 
            metadata =  sent.metadata
            sent_id = metadata["newutterance"] if "newutterance" in metadata else metadata["newutterance_id"] 
            print("sent:", sent)
            print("sent_id" , repr(sent_id))
            sent.metadata["sent_id"] = sent_id
            assert doc_id != None
        return sents

    def get_conllu2sentences(self, conllu):
        """"""
        lines = open(conllu).read()    
        matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if "newdoc_id" in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            # Use newutterance as sentence level
            # This is only case for ita.pdtb.luna
            # newutterance   : single   in a dialogue turn 
            # newutterance_id: multiple in a dialogue turn 
            metadata =  sent.metadata
            sent.metadata[self.doc_id_prefix] = metadata["newutterance"] if "newutterance" in metadata else metadata["newutterance_id"] 
            assert doc_id != None

        sentences = {}
        for sent in sents:
            # sent_id
            metadata =  sent.metadata
            sent_id = metadata["newutterance"] if "newutterance" in metadata else metadata["newutterance_id"] 
            # No text head. We get text to sent obj
            text = " ".join([obj["form"] for obj in sent])
            sentences[sent_id] = text
        return sentences


class PorPdtbCrpcProcessor(AbstractTask):
    pass

class PorPdtbTedmProcessor(AbstractTask):
    pass    


class ThaPdtbTdtbProcessor(AbstractTask):
    pass    


class TurPdtbTdbProcessor(AbstractTask):
    doc_id_prefix = "newdoc id"
    # Use parse() to parse into a list of sentences
    def conllu_to_parsed_sentences(self, conllu):
        # remove the line with adjacent tokens
        #   exmaple: 7-8 arasındaki _ _ ..
        lines = open(conllu).read()    
        matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            
            sent_id = sent.metadata[self.sent_id_prefix]
            joint_sent_id = "{}-{}".format(doc_id, sent_id)
            sent.metadata["sent_id"] = joint_sent_id
            assert doc_id != None
        return sents

    def get_conllu2sentences(self, conllu):
        lines = open(conllu).read()    
        matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            # update
            sent_id = sent.metadata[self.sent_id_prefix]
            joint_sent_id = "{}-{}".format(doc_id, sent_id)
            sent.metadata[self.sent_id_prefix] = joint_sent_id
            assert doc_id != None

        sentences = {}
        for sent in sents:
            # sent_id
            metadata =  sent.metadata
            sent_id = metadata[self.sent_id_prefix]  
            text = sent.metadata["text"] # get text from text head
            sentences[sent_id] = text
        return sentences


class TurPdtbTedmProcessor(AbstractTask):
    pass


class ZhoPdtbCdtbProcessor(AbstractTask):
    """
    The coprus does not have sentence index
    """
    doc_id_prefix = "newdoc id"
    # Use parse() to parse into a list of sentences
    def conllu_to_parsed_sentences(self, conllu):
        # remove the line with adjacent tokens
        #   exmaple: 7-8 arasındaki _ _ ..
        lines = open(conllu).read()    
        matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        sent_id = 1
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            
            joint_sent_id = "{}-{}".format(doc_id, sent_id)
            sent.metadata["sent_id"] = joint_sent_id
            sent_id += 1
            assert doc_id != None
        return sents


    def get_conllu2sentences(self, conllu):
        lines = open(conllu).read()    
        # matches = re.sub(r"\n(\d+-\d+\t.*\n)", "", lines)
        
        matches = list()
        for l in lines:
            if re.search(r"\d+-\d+", l):
                pass
            else:
                matches.append(l)
        matches = "".join(matches)

        sents = conllu_pkg.parse(matches)
        
        doc_id = None
        sent_id = 1
        for sent in sents:
            if self.doc_id_prefix in sent.metadata:
                doc_id = sent.metadata[self.doc_id_prefix]
            joint_sent_id = "{}-{}".format(doc_id, sent_id)
            sent.metadata[self.sent_id_prefix] = joint_sent_id

            sent_id += 1
            assert doc_id != None

        sentences = {}
        for sent in sents:
            # sent_id
            metadata =  sent.metadata
            sent_id = metadata[self.sent_id_prefix]  
            # text = sent.metadata["text"] # get text from text head
            # No text head. We get text to sent obj
            text = " ".join([obj["form"] for obj in sent])
            sentences[sent_id] = text
        return sentences
    


CORPUS_MAPPING = OrderedDict(
    [
        ('ita.pdtb.luna', ItaTdtbLunaProcessor),

        ("por.pdtb.crpc", PorPdtbCrpcProcessor),
        ('por.pdtb.tedm', PorPdtbTedmProcessor),
        
        ('tha.pdtb.tdtb', ThaPdtbTdtbProcessor),
        
        ('tur.pdtb.tdb', TurPdtbTdbProcessor),
        ('tur.pdtb.tedm', TurPdtbTedmProcessor),
        
        ('zho.pdtb.cdtb', ZhoPdtbCdtbProcessor),
    ]
)



class AutoTask:
    @classmethod
    def get(self, corpus_name):
        if corpus_name in CORPUS_MAPPING:
            return CORPUS_MAPPING[corpus_name]()
        raise ValueError(
            "Unrecognized corpus {} for AutoTask: {}.\n"
            "Task name should be one of {}.".format(
                ", ".join(c for c in CORPUS_MAPPING.keys())
            )
        )
