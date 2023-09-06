import os
import sys
import csv
import spacy
import align
from tqdm import tqdm

"""
This is a one-off script to align discourse relations (for now only arg1 and arg2) annotated on English translations
onto their Nigerian Pidgin original sentences. Added to this repo since it re-uses some alignment/projection
procedures, but has little to do with the grand scheme of this project/repo, so will probably be moved elsewhere
at some point.
"""

nlp = spacy.load('en_core_web_sm')
al = align.Aligner()
alignment_method = 'inter'  # options: inter, itermax, mwmf


def find_arg(arg, utt):
    results = []
    la = len(arg)
    for ind in (i for i, e in enumerate(utt) if e == arg[0]):
        if utt[ind:ind+la] == arg:
            results.append((ind, ind+la-1))
    return results


def project_arg(row, arg, en_utt, np_utt, newcolumn):
    row[newcolumn] = ''
    en_utt_tokenized = [x.text for x in nlp(row[en_utt])]
    en_raw_tokenized = [x.text for x in nlp(row[arg])]
    if not en_raw_tokenized:
        return row

    if not ' '.join(en_raw_tokenized) in ' '.join(en_utt_tokenized):
        #sys.stderr.write('WARNING: Skipped row: "%s"\nTokenization differences between entire utterance and arg raw.\n' % row)
        return row

    np_utt_tokenized = [x.text for x in nlp(row[np_utt])]

    en_range = find_arg(en_raw_tokenized, en_utt_tokenized)
    if not len(en_range) == 1:
        #sys.stderr.write('WARNING: Skipped row "%s"\nArg found more than once in utterance.\n' % row)
        return row

    en_token_ids = list(range(en_range[0][0], en_range[0][-1] + 1))

    utt_aligned = al.align(en_utt_tokenized, np_utt_tokenized)[alignment_method]
    aligned_tokens = [[a[1] for a in utt_aligned if a[0] == t] for t in en_token_ids]
    aligned_tokens = sorted(list(set([t for tl in aligned_tokens for t in tl])))
    np_raw = ' '.join([np_utt_tokenized[x] for x in aligned_tokens])
    row[newcolumn] = np_raw
    return row


def project_args(row):
    row = project_arg(row, 'arg1raw', 'EN_arg1_utt', 'NP_arg1_utt', 'NP_arg1raw')
    row = project_arg(row, 'arg2raw', 'EN_arg2_utt', 'NP_arg2_utt', 'NP_arg2raw')
    return row


def process_file(fh):
    csvd = list(csv.DictReader(open(fh), delimiter='|'))

    csvw = csv.DictWriter(open(os.path.splitext(fh)[0] + '_naijarguments_projected_%s.csv' % alignment_method, 'w', newline=''), delimiter='|', fieldnames=csvd[0])
    csvw.writeheader()
    for row in tqdm(csvd):
        newrow = project_args(row)
        csvw.writerow(newrow)


def main():
    fh = r"C:\Users\bourg\Downloads\align_arguments.txt"
    process_file(fh)


if __name__ == '__main__':
    main()
