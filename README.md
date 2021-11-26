# SynSemClass_Ger
Project to extend the multilingual verb lexicon SynSemClass (Czech and English) by including German. 
For our experiments, we use the English-German paracrawl dataset from https://paracrawl.eu/.

The repository provides scripts for:
1. preprocessing
2. word alignment with MGIZA tool
3. creating a dictionary with most common word alignments

## 1. Preprocessing

Using the paracrawl dataset, you can split the tab-separated file into two files using the command line: 
```
cut -f1 -d$'\t' file.txt> output-file.txt 
cut -f2 -d$'\t' file.txt> output-file.txt
```
In our case: 
```
cut -f1 -d$'\t' en-de.txt> paracrawl.de
cut -f2 -d$'\t' en-de.txt> paracrawl.en
```

Because of potential memory issues, it is recommended to reduce the size of dataset, example to 20mio lines:

```
head -n 20000000 paracrawl.de > paracrawl.de
head -n 20000000 paracrawl.en > paracrawl.en
```

Filter corpus for lines not ending with a dot (titles, chopped sentences, other parts from websites) and lines including more than one sentence:

```
python preproc_paracrawl_server.py --input_src paracrawl.en --input_trg paracrawl.de
```

For further preprocessing (tokenizing and lowercasing) the files we recommend to follow the tutorial: https://fabioticconi.wordpress.com/2011/01/17/how-to-do-a-word-alignment-with-giza-or-mgiza-from-parallel-corpus/.  
Save the preprocessed files inside ./dataset folder. 

## 2. Word Alignment with MGIZA tool
For working with MGIZA, you can continue to follow the tutorial or use our Dockerfile.
The Dockerfile takes the preprocessed input files, makes classes, installs and compiles MGIZA and finally, creates the word alignments.

```
docker build -f Dockerfile -t mgiza-tool . 
docker run -it --rm mgiza-tool
```

If you use the Dockerfile, you need to adjust: 

* in Dockerfile: The local path to the /dataset directory with input files in line: ``COPY $local_dir /mgiza/mgizapp/bin``. This is line only necessary when the folder is not mounted 

  (``docker run -v /dataset:/mgiza/mgizapp/bin -it --rm mgiza-tool . `` (not tested yet)) 

* in Dockerfile: Input file names (we used `paracrawl.en` for English as source language and `paracrawl.de` for German as target language).  

* Inside `configfile.txt`, you need to adjust the file-names, too. In the line “ncpus”, you can set the number of CPUs you want to use for processing. 

## 3. Creating output files for based on MGIZA output

#### 3.1 Creating a basic output with most common Word Alignments: 

The file findWord.py takes the MGIZA output-files and creates a table with the most frequent alignments from English to German verbs (threshold 0.2%). You can use the file via CL:  

```
python findWord.py -c $MGIZA_OUTPUT_FILE -w $VERB
```

In our example, searching for the most often German alignments for the verb "absorb":

```
python findWord.py -c ./output/en_de.dict.A3.final -w absorb
```

