FROM ubuntu:latest

LABEL description="MGIZA docker container for word alignment"

# Update Ubuntu.
RUN apt-get update
RUN apt-get install -y apt-utils debconf-utils
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN apt-get update && apt-get -y upgrade

# Install some necessary tools.
RUN apt-get install -y sudo nano perl python-dev python3-dev python3-pip curl wget tar 
RUN pip3 install dtrx
ADD requirements.txt .
RUN pip3 install -r requirements.txt    	 	    

# Install Moses dependencies.
RUN apt-get install -y libboost-all-dev
RUN apt-get install -y build-essential git-core pkg-config automake libtool wget zlib1g-dev python-dev libbz2-dev cmake

# Clone the repos we need.
RUN git clone https://github.com/moses-smt/mgiza.git 

# Install MGIZA++.
WORKDIR /mgiza/mgizapp
RUN cmake . && make && make install
# Edit paths in compile file; Start to compile 
RUN sed -i "s#~/workspace/github/mgiza/mgizapp/src#/mgiza/mgizapp/src#"  /mgiza/mgizapp/manual-compile/compile.sh
RUN sed -i "s#~/workspace/boost/boost_1_55_0#/boost_1_55_0#"  /mgiza/mgizapp/manual-compile/compile.sh
RUN /mgiza/mgizapp/manual-compile/compile.sh

RUN cp /mgiza/mgizapp/scripts/merge_alignment.py /mgiza/mgizapp/bin/

# Copy dataset into docker container (only necessary if not mounted)
COPY ./dataset /mgiza/mgizapp/bin

# Making classes (necessary for algorithm HMM)
WORKDIR /mgiza/mgizapp/bin

# Adjust filenames:
RUN  ./mkcls -n10 -pparacrawl.en -Vparacrawl.en.vcb.classes 
RUN  ./mkcls -n10 -pparacrawl.de -Vparacrawl.de.vcb.classes

# Translate corpus into GIZA format
RUN ./plain2snt paracrawl.en paracrawl.de
# Create the cooccurence
RUN ./snt2cooc paracrawl.en_paracrawl.de.cooc paracrawl.en.vcb paracrawl.de.vcb paracrawl.en_paracrawl.de.snt

# Copy and use config file
COPY ./configfile.txt ./
COPY ./findWord.py ./
RUN ./mgiza configfile.txt



