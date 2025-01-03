FROM ubuntu:24.04
RUN apt-get update && apt-get -y upgrade && apt-get -y install locales python3 python3-pip python3-ipython python3-docopt python3-venv
RUN pip3 install --break-system-packages --upgrade future
RUN locale-gen --lang de_DE
ADD /src/requirements.txt /requirements.txt
RUN pip3 install --break-system-packages -r /requirements.txt
# assumes host user also has UID 1000
USER ubuntu
WORKDIR /src
ADD ./src/ /src

