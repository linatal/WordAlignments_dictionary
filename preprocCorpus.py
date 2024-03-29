from nltk.tokenize import sent_tokenize
import os
import sys
import argparse
import shutil
from pathlib import Path

def create_output_dir(src_file, trg_file):
    src_dirname = os.path.dirname(src_file)
    src_dirname = os.path.join(src_dirname, '') # include / in case it is not at path ending
    output_dir = src_dirname + "dataset/"
    trg_dirname = os.path.dirname(trg_file)
    try:
        os.mkdir(output_dir) 
    except OSError:
        print ("Creation of the directory %s failed (potentially already exists)" % output_dir)
        return output_dir 
    else:
        print ("Successfully created the directory %s " % output_dir)    
    if src_dirname != os.path.join(trg_dirname, ''):
        print("Attention: src and trg files are in seperate dir, ./dataset is in src-dir ", src_dirname)
    return output_dir 



def filter_corpus(input_file):
    """filter corpus (based on German) for lines not ending with a dot (titles, chopped sentences, other parts from websites) and lines including more than one sentence"""
    with open(input_file) as f:  
        lines = f.readlines()
        indices = [i for i, s in enumerate(lines) if ".\n" in s and len(sent_tokenize(s)) < 2] 
        """
        indices = []
        for i, s in enumerate(lines1):
            if s.endswith(".\n") and len(sent_tokenize(s)) < 2:
                indices.append(i)
        """
        return indices

def delete_lines(input_file, index_list, output_dir):
    """ based on index filter both German and English corpus"""
    with open(input_file) as fi:  
        lines = fi.readlines()
        is_skipped = False
        result = []
        counter = 0
        for line in lines:
            if counter in index_list:
                result.append(line)
            else:
                is_skipped = True
            counter += 1
        # create output files
        extension = os.path.splitext(input_file)[1] # extension
        filepath = os.path.basename(input_file) # filepath + filename - file ending
        basename = os.path.splitext(filepath)[0] # only filename without file ending
        with open(output_dir + basename + "_filtered" + extension, "w") as fo:
            for line in result:
                fo.write(line) 
        return len(result)
        
def count_lines(file):
    # count lines in trg file
    count = 0
    for line in open(file).readlines(): 
        count += 1
    return count


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(description="input files")
    parser.add_argument('--input_src', metavar='path', type=str, help='the path to the input file with source language')
    parser.add_argument('--input_trg', metavar='path', type=str, help='the path to the input file with target language')
    # Execute the parse_args() method
    args = parser.parse_args()

    if not os.path.isfile(args.input_src) or not os.path.isfile(args.input_trg):
        print('The path specified does not exist, process aborted.')
        sys.exit()

    src_file = args.input_src
    trg_file = args.input_trg
    output_dir = create_output_dir(src_file, trg_file)

    len_original = count_lines(trg_file)
    print("Original dataset number of lines: ", len_original) 
    index_list = filter_corpus(trg_file)

    
    len_filtered = delete_lines(trg_file, index_list, output_dir)
    print("Left after filtering: %s lines", % len_filtered)
    
    delete_lines(src_file, index_list, output_dir)
    num = ((100 / len_original) * len_filtered)
    print("-> {:.2f} % ".format((100 / len_original) * len_filtered))
