FROM python:3.6-alpine
ADD . /fmridenoise
WORKDIR /fmridenoise
RUN pip install -r requirements.txt
