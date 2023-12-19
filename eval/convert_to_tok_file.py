import os
import re
import argparse

"""
Convert `discopyrojected.conllu` to .tok style file, which is to evaluate  evaluate segmentation f-score.
"""

def convert_to_token_file(infile, outfile):
    data = open(infile, "r").readlines()
    #data = data.replace("Seg=B-Conn","Seg=B-Conn")
    tc = 1
    num_list = list()
    with open(outfile, "w") as wf:
        for line in data:
            seq_line = line.split("\t")
            # If nwe document
            if re.search(r"# newdoc_id = ", line):
                # first document 
                wf.write(line) if tc == 1 else wf.write("\n"+line)
                tc = 1

            if re.search(r'^\d+-\d+', line):
                seq_line = [ "_" if idx not in [0,1,len(seq_line)-1] else seq_line[idx] for idx in range(len(seq_line))  ]
                # abstract the 
                num_tok = eval(seq_line[0]) + 1 
                tc_ = f"{tc}-{tc+1+num_tok}"
                seq_line[0] = str(tc_)
                line = "\t".join(seq_line)
                wf.write(line)

            if re.search(r'^\d+\t', line):
                seq_line = [ "_" if idx not in [0,1,len(seq_line)-1] else seq_line[idx] for idx in range(len(seq_line))  ]            
                seq_line[0] = str(tc)
                line = "\t".join(seq_line)
                wf.write(line)
                tc += 1
    print(f"Saving .tok file to: {outfile}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--infile", type=str, default=r"..sharedtask2023/data/tur.pdtb.tedm/tur.pdtb.tedm_test_discopyrojected.conllu")
    args = p.parse_args()
    
    infile = args.infile 
    outfile = os.path.splitext(args.infile)[0] + '.tok'
    convert_to_token_file(infile, outfile)

if __name__ == '__main__':
    main()



