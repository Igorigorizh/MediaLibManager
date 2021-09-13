FROM python:3.8-slim-buster
RUN mkdir /mnt/GoflexHome
RUN apt-get update && apt-get install -y cifs-utils  git
RUN echo "---->" $(uname -m) "<----"
RUN case $(uname -m) in *"arm"*) apt install -y libjpeg62-turbo-dev zlib1g-dev gcc;;esac
#RUN mount -t cifs -o username=igor  //192.168.1.67/ExternalUSB /mnt/GoflexHome/

WORKDIR /home/medialib
RUN  git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager

COPY medialib.db3 /home/medialib/MediaLibManager/medialib.db3
RUN pip install -r requirements.txt
EXPOSE 9001
EXPOSE 6600
CMD ["python", "./medialib/_appl_server.py" ]
