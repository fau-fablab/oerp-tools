FROM ubuntu:18.04
RUN apt-get update && apt-get -y install locales python python-pip python-ipython python-docopt
RUN locale-gen --lang de_DE
RUN pip install oerplib
WORKDIR /work
ADD . /work
