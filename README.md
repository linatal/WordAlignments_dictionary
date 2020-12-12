# SynSemClass_Ger
Project to extend the multilingual verb lexicon SynSemClass (Czech and English) by including German. 
For our experiments, we use the English-German paracrawl dataset from https://paracrawl.eu/.

The repository provides scripts for:
1. preprocessing
2. word alignment with MGIZA tool
3. creating a dictionary with most common word alignments
4. SRL (TODO)
5. including Verbs from other existing resources (TODO)

## 1. Preprocessing

Using the paracrawl dataset, you can split the tab-separated file into two files using the command line: 
```
cut -f1 -d$'\t' file.txt> output-file.txt 
cut -f2 -d$'\t' file.txt> output-file.txt
```
In our case: 
```
cut -f1 -d$'\t' en-de.txt> en.txt 
cut -f2 -d$'\t' en-de.txt> de.txt 
```

For preprocessing (tokenizing and lowercasing) the files we recommend to follow the tutorial: https://fabioticconi.wordpress.com/2011/01/17/how-to-do-a-word-alignment-with-giza-or-mgiza-from-parallel-corpus/.  
Save the preprocessed files inside dataset folder. 

## 2. Word Alignment with MGIZA tool
For working with MGIZA, you can continue to follow the tutorial or use our Dockerfile.
The Dockerfile takes the preprocessed input files, makes classes, installs and compiles MGIZA and finally, creates the word alignments.
If you use the Dockerfile, you just need to adjust the input file names (we used `paracrawl.en` for English as source language and `paracrawl.de` for German as target language).  
Inside `configfile.txt`, you need to adjust the file-names, too. In the line “ncpus”, you can set the number of CPUs you want to use for processing. 

## 3. Creating a Dictionary with most common Word Alignments

The file findWord.py takes the MGIZA output-files and creates a dictionary with the most frequent alignments from English to German verbs (threshold 0.2%). You can use the file via CL:  
`findWord.py -c mgiza-output.txt -w $VERB`
