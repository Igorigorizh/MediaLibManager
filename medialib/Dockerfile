FROM python:3.10-slim-buster
RUN apt-get update && apt-get install -y cifs-utils  git shntool ffmpeg libdiscid0
RUN echo "---->" $(uname -m) "<----"
RUN case $(uname -m) in *"arm"*) apt install -y libjpeg62-turbo-dev zlib1g-dev gcc;;esac

WORKDIR /home/medialib
COPY requirements.txt /home/medialib/requirements.txt
RUN pip3 install -r requirements.txt


ARG CACHE_VER="unknown"
RUN echo "medialib cache ver is ${CACHE_VER}"
RUN CACHE_VER=${CACHE_VER} git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager

EXPOSE 9001
EXPOSE 6600
CMD ["python", "./medialib/_appl_server.py" ]
