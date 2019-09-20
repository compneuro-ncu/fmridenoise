FROM continuumio/miniconda3
RUN apt-get update
RUN apt-get install gcc -y
RUN pip install fmridenoise
ADD . /fmridenoise
WORKDIR /fmridenoise
ENTRYPOINT /bin/sh

