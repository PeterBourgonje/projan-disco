# projan-disco

[**Prerequisites**](#prerequisites) | [**Usage**](#usage) | [**Evaluation**](#evaluation)]

A pipeline for multi-lingual Shallow Discourse Parsing, based on annotation projection.

# Prerequisites
This code relies on a dockerized version of [discopy](https://github.com/rknaebel/discopy) running on your localhost.
Download and run this like so:
```
docker pull rknaebel/discopy:1.0.2
docker run -it --rm  -p 8080:8080 rknaebel/discopy:1.0.2
```
Also, you'll need a working API key for the translation API of your choice. Export this as a system environment variable, e.g. if you're using DeepL, on linux:
```
export DEEPL_API_KEY=your-own-personal-deepl-key...
```
Lastly, you'll need to install the requirements:
```
pip install -r requirements.txt
```

# Usage
Once the above prerequisites are met, the pipeline can be used like so (see also ```main``` in ```project.py```):
```
import spacy
import translate
import project

nlp_de = spacy.load('de_core_news_sm')
trans = translate.AutoTranslator.get('deepl')
pd = project.ProjanDisco()

input_text = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'
src_sentences = [[t.text for t in s] for s in nlp_de(input_text).sents]
trg_sentences = [trans.translate(' '.join(s), 'EN-US').split() for s in src_sentences]

projected = pd.annotate(src_sentences, trg_sentences)

import json
print(json.dumps(projected, indent=2, ensure_ascii=False))
```
This snippet would return:
```
[
  {
    "Arg1": {
      "RawText": "die Wirtschaft rückläufig ist",
      "TokenList": [
        9,
        10,
        12,
        13
      ]
    },
    "Arg2": {
      "RawText": "",
      "TokenList": []
    },
    "Connective": {
      "RawText": "Obwohl",
      "TokenList": [
        8
      ]
    },
    "DocID": -8918892796650016165,
    "ID": 0,
    "Sense": [
      "Comparison.Contrast"
    ],
    "Type": "Explicit"
  }
]
```

# Evaluation

The following sections describe how to reproduce the results from our paper.

Clone the official [sharedtask2023 repository](https://github.com/disrpt/sharedtask2023) to get the data and [evaluation script](https://github.com/disrpt/sharedtask2023/blob/main/utils/seg_eval.py). Note that some corpora are behind LDC paywall, and the [process_underscores.py](https://github.com/disrpt/sharedtask2023/blob/main/utils/process_underscores.py) script will need to be run in order to insert the actual tokens.
Set the `PATH` according to where you cloned the shared task repository on your machine. 

### Corpora

In our paper, we include the following seven corpora:

| Corpus          | Language   |
| --------------- | ---------- |
| ita.pdtb.luna   | Italian    |
| por.pdtb.crpc   | Portuguese |
| por.pdtb.tedm   | Portuguese |
| tha.pdtb.tdtb   | Thai       |
| tur.pdtb.tdb    | Turkish    |
| tur.pdtb.tedm   | Turkish    |
| zho.pdtb.cdtb   | Chinese    |

### Translating and Projecting Annotation

`eval/disrpt_eval.py` projects annotations to the given non-English input file. Intermediate files for translation results and parsing results are saved for intermediate analysis, under the filename specified by `outname`. The two files will be saved in `--dump_translation_dir` and `--dump_trans_dir`.

To change the API of the translator or aligner, specify the corresponding flag name.

* `--translator_api` supports `deepl` and`google`
* `--aligner_api` supports `simalign` and `awesome`

Make sure to set the API key is you are using the DeepL translator (either hard-coded, or export it as a system environment variable, see the first few lines of `translate.py`). For Google Translate, no API key is needed. Also make sure that the port number in the code (8080) matches that of the docker container running discopy. 

Run the following sample code to get annotations projected for `tur.pdtb.tedm_test.conllu`:

```bash
python eval/disrpt_eval.py \
    --infile=PATH/tur.pdtb.tedm_test.conllu \
    --outname=PATH/tur.pdtb.tedm_test.pt-en.json \
    --dump_translation_dir=PATH \
    --dump_parser_dir=PATH \
    --aligner_api=simalign \
    --translator_api=deepl \
    --pred_output_dir=PATH
```

When evaluation is completed, the result will be saved in the directory of `pred_output_dir` with `_discopyrojected.conllu` appended to the input filename. For instance, `pred_output_dir/tur.pdtb.tedm_test_discopyrojected.conllu`.


### Format Conversion

We evaluate connective identification by one token per line, with no sentence breaks (default *.tok format) using the .tok gold file.

Run the following command to convert PATH/por.pdtb.crpc_test_discopyrojected.conllu to .tok. This will save a .tok file that can be used to compare against the gold file from the shared task data set.

```bash
python convert_to_tok_file \
    --infile=pred_output_dir/tur.pdtb.tedm_test_discopyrojected.conllu
```

Next, run the official evaluation script to get the final score.

```
EXPORT PREDS=PATH/tur.pdtb.tedm_test_discopyrojected.tok
EXPORT GOLD=PATH/tur.pdtb.tedm_test.tok
python3 PATH/sharedtask2023/utils/seg_eval.py $GOLD $PREDS
```

### Citation

If you use the code in this repository, please cite the following:

```
@inproceedings{bourgonje-lin-2024-projecting,
    title = "Projecting Annotations for Discourse Relations: Connective Identification for Low-Resource Languages",
    author = "Bourgonje, Peter  and
      Lin, Pin-Jie",
    editor = "Strube, Michael  and
      Braud, Chloe  and
      Hardmeier, Christian  and
      Li, Junyi Jessy  and
      Loaiciga, Sharid  and
      Zeldes, Amir  and
      Li, Chuyuan",
    booktitle = "Proceedings of the 5th Workshop on Computational Approaches to Discourse (CODI 2024)",
    month = mar,
    year = "2024",
    address = "St. Julians, Malta",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2024.codi-1.4",
    pages = "39--49",
    abstract = "We present a pipeline for multi-lingual Shallow Discourse Parsing. The pipeline exploits Machine Translation and Word Alignment, by translating any incoming non-English input text into English, applying an English discourse parser, and projecting the found relations onto the original input text through word alignments. While the purpose of the pipeline is to provide rudimentary discourse relation annotations for low-resource languages, in order to get an idea of performance, we evaluate it on the sub-task of discourse connective identification for several languages for which gold data are available. We experiment with different setups of our modular pipeline architecture and analyze intermediate results. Our code is made available on GitHub.",
}

```

