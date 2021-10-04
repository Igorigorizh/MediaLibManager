FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y cifs-utils  git
RUN echo "---->" $(uname -m) "<----"
RUN case $(uname -m) in *"arm"*) apt install -y libjpeg62-turbo-dev zlib1g-dev gcc;;esac

WORKDIR /home/medialib
COPY requirements.txt /home/medialib/requirements.txt
RUN pip install -r requirements.txt

ARG medialib_bld_ver="unknown"
RUN echo "medialib build ver is ${medialib_bld_ver}"
RUN medialib_bld_ver=${medialib_bld_ver} git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager

EXPOSE 9001
EXPOSE 6600
CMD ["python", "./medialib/_appl_server.py" ]
