import sys
import re
import string
from collections import defaultdict
from optparse import OptionParser
import os
import codecs
import numpy
import itertools
import json
import pandas as pd 
import argparse

#classname = "base"
#class_id = "vec00179"
#mgiza_output = "/data/experiments/kzaczynska/mgiza/paracrawl/output-quater-f/en_de.dict.A3.final"
#srclang_file = "/data/experiments/kzaczynska/mgiza/paracrawl/en-de-quater-f/paracrawl-f.en"
#trglang_file = "/data/experiments/kzaczynska/mgiza/paracrawl/en-de-quater-f/paracrawl-f.de"
#output_path = f"/data/experiments/kzaczynska/mgiza/postprocessing_paracrawl/output_tables_ordered/candidate_sentences_{classname}_{class_id}.txt"
#output_path_candidates = f"/data/experiments/kzaczynska/mgiza/postprocessing_paracrawl/findSentence_scripts/output_tables_ordered/new_german_verbs/candidate_verbs_{classname}_{class_id}.txt"

candidate_verbs_list = []

def create_output_dir(srclang_file, trglang_file):
    src_dirname = os.path.dirname(srclang_file)
    src_dirname = os.path.join(src_dirname, '') # include / in case it is not at path ending
    output_dir = src_dirname + "synsem_outputfiles/"
    trg_dirname = os.path.dirname(trglang_file)
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


def parseCorpusToDict(corpusFile):

    src2trg = defaultdict(lambda : defaultdict(float))
    flines = codecs.open(corpusFile, "r", encoding = "utf-8").readlines()
    triple_list = []
    index_alignment = []
    sent_index_list = []

    for i, line in enumerate(flines):

        line = line.strip()
        if line.startswith('#'):
            if re.findall(r"\((\d+)\)", line):
                sent_index = re.findall(r"\((\d+)\)", line)[0]
            #print(sent_index_list)
            deSent = flines[i+1]
            #print(sent_index_list, deSent)
            enSent = flines[i+2] # this and the line above should not lead to OutOfIndexErrors if the syntax is correct
            end = defaultdict(str)
            for i2, word in enumerate(deSent.split()):
                end[i2+1] = word # alignment is not zero-based
            for m in re.finditer(r"(\w+) \(\{([\d\s]+)\}\)", enSent): # maybe I'll also want to do something with the NULL at the start of the line (for words not literally found in the translation I guess)
                enWord = m.groups()[0]
                deIndex = m.groups()[1].split()
                deWord = " ".join([end[int(i3)] for i3 in deIndex])
                # only two word entrance per 1 engl verb
                if len(deWord.split()) <= 2: 
                    src2trg[enWord][deWord] += 1 
                #src2trg[enWord][deWord] += 1  
                triple = (enWord, deWord, sent_index)
                triple_list.append(triple)   

    # normalize dict to probabilities
    for w in src2trg:
        total = 0
        for sw in src2trg[w]:
            total += src2trg[w][sw]
        for sw in src2trg[w]:
            src2trg[w][sw] = src2trg[w][sw] / total

    return (src2trg, triple_list)

def findSingleWord(word, src2trg, threshold):
    if threshold == None:
        threshold = 0.02
    out = defaultdict(float)
    for trg in src2trg[word]:
        if src2trg[word][trg] > threshold:
            out[tuple(trg)] = src2trg[word][trg]
    return out



def triples_into_list(triples):
    triples_list = []
    for triple in triples:
        triples_list.append(list(triple))
    return triples_list




def createIndexAlignemnt(json_alignm, triples_list):
    data = []
    for verb_en, val_de in json_alignm.items():
        for verb_de in val_de:
            for t in triples_list:
                if t[0] == verb_en and t[1] == verb_de:
                    data.append(t)
    df = groupDataFrame(data)
    return df

def groupDataFrame(data_list):
    df = pd.DataFrame(data_list, columns=['en_verb', 'de_verb', 'index_all_align'])
    df = df.groupby(['en_verb', 'de_verb'])['index_all_align'].apply(list).reset_index()
    df['index_all_align'] = df['index_all_align']
    return df


def createReducedIndexList(df):
    # get sentences from index
    index_list = df['index_all_align'].tolist()
    reduced_list = []
    for alignments in index_list:
        reduced_list.append(alignments[:19])####number of sentences?
    return reduced_list

def create_en_df(reduced_list, df):
    # english
    df_en = df.copy()
    flines_en = open(srclang_file, "r", encoding = "utf-8").readlines()
    big_list_en =  indexToSent(reduced_list, flines_en)
    df_en["sentences"] = big_list_en
    df_en.insert(3, "lang", "en")
    # separate sentence-lists into sentence per row
    df_en = df_en.explode("sentences").replace('\n','', regex=True).reset_index(drop=True)
    #df_en.to_csv(f'output_tsf_en_{classname}.txt', sep='\t', header=True)
    return df_en

def create_de_df(reduced_list, df_de):
    # german 
    flines_de = open(trglang_file, "r", encoding = "utf-8").readlines()
    big_list_de =  indexToSent(reduced_list, flines_de)
    df_de["sentences"] = big_list_de
    df_de.insert(3, "lang", "de")
    df_de = df_de.explode("sentences").replace('\n','', regex=True).reset_index(drop=True)
    #df_de.to_csv(f'output_tsf_de_{classname}.txt', sep='\t', header=True)
    return df_de

def indexToSent(reduced_list, flines):
    big_list = [] 
    for rlist in reduced_list:
        sentence_list = []
        for i_list in rlist:
            sentence_list.append(flines[int(i_list)-1])
        big_list.append(sentence_list)
    return big_list
 
if __name__ == '__main__':
    
    # Create the parser
    parser = argparse.ArgumentParser(description="input classnames paths")
    parser.add_argument("-cn", '--classname', type=str, help='include classname')
    parser.add_argument("-cid", '--classid', type=str, help='include classid vec00XXX')
    parser.add_argument("-mo", '--mgiza_output', type=str, help='path to mgiza output file')
    parser.add_argument("-i1", '--input_src', type=str, help='the path to the input file with source language')
    parser.add_argument("-i2", '--input_trg', type=str, help='the path to the input file with target language')
    #parser.add_argument("-v", '--ref_verbs', nargs='+', help='list of verbs in src lang used to search for word alignments in trg lang')
    parser.add_argument('-l', '--list', help='comma-delimited list input', type=lambda s: [str(item) for item in s.split(',')])
    # Execute the parse_args() method
    args = parser.parse_args()

    if not os.path.isfile(args.input_src) or not os.path.isfile(args.input_trg):
        print('The path specified does not exist')
        sys.exit()

    classname = args.classname
    class_id = args.classid
    srclang_file = args.input_src
    trglang_file = args.input_trg
    mgiza_output = args.mgiza_output
    print(args.list)
    rfc_verbs = args.list
    #rfc_verbs = ["arrange" , "assemble" , "base" , "build" , "co-found" , "construct" , "create" , "develop" , "enact" , "enforce" , "engineer" , "establish" , "float" , "form" , "found" , "generate" , "hit" , "implement" , "institute" , "introduce" , "launch" , "open"  , "organize" , "produce" , "provide" , "raise" , "reinstate" , "reopen" , "restart" , "run" , "set" , "spur" , "start" , "take" , "trigger"]  
    
    output_dir = create_output_dir(srclang_file, trglang_file)
    # pipe output to logfile
    sys.stdout = open(output_dir + f"logfile_{classname}_{class_id}.txt", 'w')
    
    src2trg, triples = parseCorpusToDict(mgiza_output)
    
    triples_list = triples_into_list(triples)

    outdict = None
    for word in rfc_verbs:
        print(word)

        inputLength = len(word.split())
        json_alignm = {}
        json_alignm[word] = []
        # NOTE: for single words, it's faster/more efficient to first build the alignment dict (on word level basis) and then do simple lookups. For phrases, the original alignment file is needed to check for each individual case if/how every word in the phrase is translated (in the particlar context).
        
        if inputLength == 1:
            outdict = findSingleWord(word, src2trg, 0.002)
            #print(outdict)
        else:
            print("Insert only one input word.")
            
        # create lists for candidate verbs file candidate_verbs
        for key in sorted(outdict, key=outdict.get, reverse=True):
            candidate_verbs_rows = []
            print("%s\t%s" % (''.join(key), str(outdict[key])))
            json_alignm[word].append(''.join(key))
            candidate_verbs_rows.append(word)
            candidate_verbs_rows.append(class_id)
            candidate_verbs_rows.append(''.join(key))
            candidate_verbs_rows.append('')
            candidate_verbs_rows.append('')
            candidate_verbs_rows.append('')
            candidate_verbs_rows.append('')
            candidate_verbs_list.append(candidate_verbs_rows)
        #print(candidate_verbs_list)
        
        # create candidate verbs file
        df_candidate_verbs = pd.DataFrame(candidate_verbs_list,columns=['class', 'classID', 'phrase', 'lemma', 'import', 'comment', 'restr'])
        output_file_verbs = output_dir + f"candidate_verbs_{classname}_{class_id}.csv"
        df_candidate_verbs.to_csv(output_file_verbs, sep='\t', mode = "w", encoding = "utf-8", index=False)

        BaseDataFrame = createIndexAlignemnt(json_alignm, triples_list)
        ReducedList = createReducedIndexList(BaseDataFrame)
        df_en = create_en_df(ReducedList, BaseDataFrame)
        df_de = create_de_df(ReducedList, BaseDataFrame)

        
        #df_concat = pd.concat([df_en, df_de]).sort_index().reset_index(drop=True)
        df_concat = pd.concat([df_en, df_de]).sort_index().reset_index()
        df_concat = df_concat.drop(["index_all_align"], axis = 1)
        output_file_sents = output_dir + f"candidate_sentences_{classname}_{class_id}.csv"
        df_concat.to_csv(output_file_sents, sep='\t', header=not os.path.exists(output_file_sents), mode = "a", encoding = "utf-8")
    
    sys.stdout.close()


    
