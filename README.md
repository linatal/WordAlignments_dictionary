# SynSemClass_Ger
Project to extend the multilingual verb lexicon SynSemClass (Czech and English) by including German. 
For our experiments, we use the English-German paracrawl dataset from https://paracrawl.eu/.

The repository provides scripts for:
1. preprocessing
2. word alignment with MGIZA tool
3. creating a dictionary with most common word alignments

## 1. Preprocessing

#### Split file into two files

Using the paracrawl dataset, you can split the tab-separated file into two files using the command line: 

```
cut -f1 -d$'\t' file.txt> output-file.txt 
cut -f2 -d$'\t' file.txt> output-file.txt
```
In our case: 
```
cut -f2 -d$'\t' en-de.txt> paracrawl.en
cut -f1 -d$'\t' en-de.txt> paracrawl.de
```

#### Reduce filesize (optional)

Because of potential memory issues, it is recommended to reduce the size of dataset, example to 20mio lines:

```
head -n 20000000 paracrawl.de > paracrawl.de
head -n 20000000 paracrawl.en > paracrawl.en
```

#### Filter non-sentences

Filter corpus for lines not ending with a dot (titles, chopped sentences, other parts from websites) and lines including more than one sentence:

```
python preprocCorpus.py --input_src $PATH_TO_CORPUS_SRC_LANG --input_trg $PATH_TO_CORPUS_TRG_LANG
```

In our example:

```
python preprocCorpus.py --input_src paracrawl.en --input_trg paracrawl.de
```

#### Further preprocessing (tokenizing and lowercasing)

For further preprocessing (tokenizing and lowercasing) the files we recommend to follow the tutorial: https://fabioticconi.wordpress.com/2011/01/17/how-to-do-a-word-alignment-with-giza-or-mgiza-from-parallel-corpus/.  
Save the preprocessed files inside ./dataset folder. 



## 2. Word Alignment with MGIZA Tool
For working with MGIZA, you can continue to follow the tutorial or use our Dockerfile.
The Dockerfile takes the preprocessed input files, makes classes, installs and compiles MGIZA and finally, creates the word alignments.

```
docker build -f Dockerfile -t mgiza-tool . 
docker run -it --rm mgiza-tool
```

If you use the Dockerfile, you need to adjust: 

* in Dockerfile: The local path to the ./dataset directory with input files in line: ``COPY $local_dir /mgiza/mgizapp/bin``. This is line only necessary when the folder is not mounted 

  (``docker run -v /dataset:/mgiza/mgizapp/bin -it --rm mgiza-tool . `` (not tested yet)) 

* in Dockerfile: Input file names (we used `paracrawl.en` for English as source language and `paracrawl.de` for German as target language).  

* Inside `configfile.txt`, you need to adjust the file-names, too. In the line “ncpus”, you can set the number of CPUs you want to use for processing. 

## 3. Creating a Basic Output with Most Common Word Alignments: 

`findWord.py` takes the MGIZA output-files and creates a table with the most frequent alignments from English to German verbs (threshold 0.2%). You can use the file via CL:  

```
python3 findWord.py -c $PATH_TO_MGIZA_OUTPUT_FILE -w $VERB
```

In our example, searching for the most often German alignments for the verb "absorb":

```
python3 findWord.py -c ./output/en_de.dict.A3.final.part000 -w absorb
```

## 4. Create Output Files for SynSemClass Project

#### Overview and Output Files

For the SynSemClass project, we need two output files per synonym class. `createOutputFiles.py` takes the MGIZA output-file and filtered corpus files and creates: 

1. a file with most common word alignments: `candidate_verbs_{VERB_NAME}_{CLASS_NAME}.csv`
2. a file with verbs and candidate example sentences:  `candidate_sentences_{EN-VERB_NAME}_{CLASS_NAME}.csv`
3. a logfile `logfile_{classname}_{class_id}.csv`



#### Template Command:

```
python3 createOutputFiles.py \
--classname $SYNSEM_CLASS_VERB_NAME \
--classid $SYNSEM_CLASS_NAME \
--mgiza_output $PATH_TO_MGIZA_OUTPUTFILE \
--input_src $PATH_TO_CORPUS_SRC_LANG \
--input_trg $PATH_TO_CORPUS_TRG_LANG \
--ref_verbs $VERBLIST_SRC_LANG # comma-separated verb list without spaces
```

#### Example Command:

```
python3 createOutputFiles.py \
--classname base \
--classid vec00179 \
--mgiza_output ./SynSemClass_Ger_Extension/input_files/en_de_mini.dict.A3.final.part000 \
--input_trg ./SynSemClass_Ger_Extension/input_files/paracrawl.de \
--input_src ./SynSemClass_Ger_Extension/input_files/paracrawl.en \
--list arrange,assemble,base,build,construct,create,develop
```

#### Explanation Flags:

- -cn, --classname: include verb classname

* -cid, --classid: include classid vec00XXX
* -mo, --mgiza_output: path to mgiza output dictionary
* -i1, --input_src: the path to the input file with source language (corpus before tokenization or lowercasing)
* -i2, --input_trg: the path to the input file with target language (corpus before tokenization or lowercasing)
*  -l, --list: comma-delimited list input with no spaces



For `--list`, include those English verbs belonging to the class as comma-separated list (no spaces). To create the list, you can:

- go to source code of synsemclass website, search for tag`<span class="cms_label" title="Classmembers for class"...`

- copy list of english verbs + IDs

- you can serialize english verbs as list without id's via commandline using this example as template:

```
echo "ask (EngVallex-ID-ev-w141f2), inquire (EngVallex-ID-ev-w1710f1), interview (EngVallex-ID-ev-w1741f1), poll (EngVallex-ID-ev-w2324f1), question (EngVallex-ID-ev-w2465f2)" | sed 's/([^()]*)//g' | tr -d ' '
```

TODO: simplify this step by including a list of class-ids + verbs ??
