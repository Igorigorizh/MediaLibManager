FROM python:3.8-slim-buster
RUN apt-get update && apt-get install -y cifs-utils apache2 apache2-utils ssl-cert libapache2-mod-wsgi-py3 git
RUN echo "---->" $(uname -m) "<----"
RUN case $(uname -m) in *"arm"*) apt install -y libjpeg62-turbo-dev zlib1g-dev gcc;;esac
WORKDIR /home/medialib
COPY requirements.txt /home/medialib/requirements.txt
RUN pip install -r requirements.txt

ARG wsgi_bld_ver="unknown"
RUN echo "wsgi build ver is ${wsgi_bld_ver}"
RUN CACHE_VER=${wsgi_bld_ver} git clone https://github.com/Igorigorizh/MediaLibManager.git
WORKDIR /home/medialib/MediaLibManager

RUN cp ./www/apache2-conf/mod-wsgi.conf /etc/apache2/conf-available/mod-wsgi.conf
RUN cp ./www/apache2-conf/apache2.conf /etc/apache2/apache2.conf
RUN cp ./www/apache2-conf/index.html /var/www/html/index.html
RUN mkdir /var/www/wsgi
RUN mkdir /var/www/wsgi/medialib
RUN mkdir /var/www/wsgi/images

RUN cp ./www/wsgi/medialib/hello.wsgi /var/www/wsgi/medialib/hello.wsgi
RUN cp ./www/wsgi/images/image.wsgi /var/www/wsgi/images/image.wsgi
RUN cp -r ./www/static/css /var/www/html/
RUN cp -r ./www/static/js /var/www/html/
RUN cp -r ./www/static/image /var/www/html/

RUN a2enconf mod-wsgi
EXPOSE 80
CMD ["apachectl", "-DFOREGROUND"]
