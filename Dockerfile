# --system configuration--
FROM ubuntu:focal
RUN apt update
RUN apt upgrade
RUN apt install -y python3 python3-pip
# --fmridenoise installation
ADD . /fmridenoise-src
WORKDIR /fmridenoise-src
RUN python3 setup.py install
# --fmridenoise run
ENTRYPOINT ["fmridenoise"]