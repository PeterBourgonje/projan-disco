# projan-disco

[**Prerequisites**](#prerequisites) | [**Usage**](#usage) | [**Reproduce Main Result**](#reproduce-main-result)]

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

# Reproduce Main Result

To reproduce the results from Table 2, follow these steps and set the `PATH` according to your repository. Clone the official [sharedtask2023 repo](https://github.com/disrpt/sharedtask2023) to get evaluation scirpt.

### Corpora

The table displays seven corpora used in Table 2:

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

`disrpt_eval.py` performs both translation and projecting annotation to the given non-English test files. We save intermediate files for translation results and parsing results with the filename specified by `outname`. The two files will be saved in `--dump_translation_dir` and `--dump_trans_dir` for easier analysis of potential misannotations.

Note that to change the API of the translator or aligner, one needs to specify the corresponding flag name.

* `--translator_api` supports `deepl` and`google`
* `--aligner_api` supports `simalign` and `awesome`

Make sure to set the API key for using the DeepL translator if you specify using the DeepL translator. Google translator is API-free. Also make sure you use identical port, e.g. 8080, to `discorpase.py.py` as port of docker container. 

Run the following sample code to get annotation on `tur.pdtb.tedm_test.conllu`:

```bash
python disrpt_eval.py \
    --infile=PATH/tur.pdtb.tedm_test.conllu \
    --outname=PATH/tur.pdtb.tedm_test.pt-en.json \
    --dump_translation_dir=PATH \
    --dump_parser_dir=PATH \
    --aligner_api=simalign \
    --translator_api=deepl \
    --pred_output_dir=PATH
```

Once the program is done, a projection result will be saved in the directory of pred_output_dir with `_discopyrojected.conllu` as the file ending. For instance, `pred_output_dir/tur.pdtb.tedm_test_discopyrojected.conllu`.


### Evaluation

We evaluate connective identification by one token per line, with no sentence breaks (default *.tok format) using the .tok gold file.

Run the command to convert PATH/por.pdtb.crpc_test_discopyrojected.conllu to .tok. This will save a .tok file as the gold file in sharedtask2023.

```bash
python convert_to_tok_file \
    --infile=pred_output_dir/tur.pdtb.tedm_test_discopyrojected.conllu
```

Next, run the official evaluation script with the command, and you will get the evaluation score.

```
EXPORT PREDS=PATH/tur.pdtb.tedm_test_discopyrojected.tok
EXPORT GOLD=PATH/tur.pdtb.tedm_test.tok
python3 PATH/sharedtask2023/utils/seg_eval.py $GOLD $PREDS
```


