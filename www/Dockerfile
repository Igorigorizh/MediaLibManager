FROM python:3.8-slim-buster
RUN mkdir /mnt/GoflexHome
RUN apt-get update && apt-get install -y cifs-utils apache2 apache2-utils ssl-c$

WORKDIR /home/medialib
RUN  git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager

RUN cp ./wsgi/apache2-conf/mod-wsgi.conf /etc/apache2/conf-available/mod-wsgi.c$
RUN cp ./wsgi/apache2-conf/apache2.conf /etc/apache2/apache2.conf
RUN cp ./wsgi/apache2-conf/index.html /var/www/html/index.html
RUN mkdir /var/www/wsgi
RUN mkdir /var/www/wsgi/medialib
RUN mkdir /var/www/wsgi/images

RUN cp ./wsgi/medialib/hello.wsgi /var/www/wsgi/medialib/hello.wsgi
RUN cp ./wsgi/images/image.wsgi /var/www/wsgi/images/image.wsgi
RUN cp -r ./wsgi/static/css /var/www/html/
RUN cp -r ./wsgi/static/js /var/www/html/
RUN cp -r ./wsgi/static/image /var/www/html/

RUN a2enconf mod-wsgi

RUN pip install -r requirements.txt


COPY /MediaLibManager/medialib.db3 /home/medialib/MediaLibManager/medialib.db3
EXPOSE 80
CMD ["apachectl", "-DFOREGROUND"]