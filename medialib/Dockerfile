FROM python:3.10-slim-buster
RUN apt-get update && apt-get install -y cifs-utils  git shntool ffmpeg libdiscid0
RUN echo "---->" $(uname -m) "<----"
RUN case $(uname -m) in *"arm"*) apt install -y libjpeg62-turbo-dev zlib1g-dev gcc;;esac

WORKDIR /home/medialib
COPY requirements.txt /home/medialib/requirements.txt
RUN pip3 install -r requirements.txt

ARG medialib_bld_ver="unknown"
RUN echo "medialib build ver is ${medialib_bld_ver}"
RUN medialib_bld_ver=${medialib_bld_ver} git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager
ENV PYTHONPATH="$PYTHONPATH:./medialib"
