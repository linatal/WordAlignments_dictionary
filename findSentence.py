

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

original_file_en = "/Users/karolinazaczynska/Documents/DFKI/datasets/paracrawl/en-de5m-preproc/paracrawl5m.en"
original_file_de = "/Users/karolinazaczynska/Documents/DFKI/datasets/paracrawl/en-de5m-preproc/paracrawl5m.de"

def parseCorpusToDict(corpusFile):

    src2trg = defaultdict(lambda : defaultdict(float))
    flines = codecs.open(corpusFile, "r").readlines()
    triple_list = []
    index_alignment = []
    sent_index_list = []

    for i, line in enumerate(flines):

        line = line.strip()
        if line.startswith('#'):
            if re.findall(r"\((\d+)\)", line):
                sent_index = re.findall(r"\((\d+)\)", line)[0]
                #sent_index_list.append(sent_index)
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
                src2trg[enWord][deWord] += 1  
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
        threshold = 0.5
    out = defaultdict(float)
    for trg in src2trg[word]:
        if src2trg[word][trg] > threshold:
            out[tuple(trg)] = src2trg[word][trg]
    return out



def groupDataFrame(data_list):
    df = pd.DataFrame(data_list, columns=['en_verb', 'de_verb', 'index_all_align'])
    df = df.groupby(['en_verb', 'de_verb'])['index_all_align'].apply(list).reset_index()
    df['index_all_align'] = df['index_all_align']
    return df

def triples_into_list(triples):
    triples_list = []
    for triple in triples:
        triples_list.append(list(triple))
    return triples_list


#### hier weitermachen!!!!

def createIndexAlignemnt(json_alignm):
    data = []
    for verb_en, val_de in json_alignm.items():
        for verb_de in val_de:
            for t in triples_list:
                if t[0] == verb_en and t[1] == verb_de:
                    data.append(t)
    df = groupDataFrame(data)
    return df

def createReducedIndexList(df):
    # get sentences from index
    index_list = df['index_all_align'].tolist()
    reduced_list = []
    for alignments in index_list:
        reduced_list.append(alignments[:3])
    return reduced_list

def create_en_df(reduced_list, df):
    # english
    df_en = df.copy()
    flines_en = open(original_file_en, "r").readlines()
    big_list_en =  indexToSent(reduced_list, flines_en)
    df_en["sentences"] = big_list_en
    df_en.insert(3, "lang", "en")
    # separate sentence-lists into sentence per row
    df_en = df_en.explode("sentences").replace('\n','', regex=True).reset_index(drop=True)
    df_en.to_csv('output_tsf_en.txt', sep='\t', header=True)
    return df_en

def create_de_df(reduced_list, df_de):
    # german 
    flines_de = open(original_file_de, "r").readlines()
    big_list_de =  indexToSent(reduced_list, flines_de)
    df_de["sentences"] = big_list_de
    df_de.insert(3, "lang", "de")
    df_de = df_de.explode("sentences").replace('\n','', regex=True).reset_index(drop=True)
    df_de.to_csv('output_tsf_de.txt', sep='\t', header=True)
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
   
    parser = OptionParser("usage: %prog corpus")
    parser.add_option("-w", "--word", dest="word", help="specify source word to look for in alignment corpus (de-en)...")
    # replaced with "aligned_file"
    parser.add_option("-c", "--corpus", dest="corpus", help="aligned corpus, de-en")

    options, args = parser.parse_args()
    
    if not options.word or not options.corpus:
        parser.print_help(sys.stderr)
        sys.exit(1)
    
    src2trg, triples = parseCorpusToDict(options.corpus)
    triples_list = triples_into_list(triples)

    outdict = None
    inputLength = len(options.word.split())
    json_alignm = {}
    json_alignm[options.word] = []
    # NOTE: for single words, it's faster/more efficient to first build the alignment dict (on word level basis) and then do simple lookups. For phrases, the original alignment file is needed to check for each individual case if/how every word in the phrase is translated (in the particlar context).
    
    if inputLength == 1:
        outdict = findSingleWord(options.word, src2trg, 0.002)
        print(outdict)
    else:
        outdict = findPhrase(options.word, options.corpus, 0.002)

    for key in sorted(outdict, key=outdict.get, reverse=True):
        print("%s\t%s" % (''.join(key), str(outdict[key])))
        json_alignm[options.word].append(''.join(key))
    print(json_alignm)
    BaseDataFrame = createIndexAlignemnt(json_alignm)
    ReducedList = createReducedIndexList(BaseDataFrame)
    df_en = create_en_df(ReducedList, BaseDataFrame)
    df_de = create_de_df(ReducedList, BaseDataFrame)

    df_concat = pd.concat([df_en, df_de]).sort_index().reset_index(drop=True)
    df_concat = df_concat.drop(["index_all_align"], axis = 1)
    
    df_concat.to_csv('output_tsf_concat.txt', sep='\t', header=True, mode = "a")



    
    
