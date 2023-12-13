# projan-disco

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

nlp_de = spacy.load('de_core_news_sm') # spacy is only used for sentence-splitting and tokenization. Feel free to use your own, preferred method here instead.
trans = translate.Translator()
pd = ProjanDisco()

input_text = 'Die Aktienkurse sind seit letztem Monat gestiegen. Obwohl die Wirtschaft allgemein rückläufig ist.'

src_sentences = [[t.text for t in s] for s in nlp_de(input_text).sents]
trg_sentences = [trans.translate(' '.join(s), 'EN-US').split() for s in src_sentences] # this does white-space tokenization. Might want to use something more sophisticated here instead.
projected = pd.annotate(src_sentences, trg_sentences)

import json
print(json.dumps(projected, indent=2))
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

