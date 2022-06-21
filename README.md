# MediaLibManager
Linux compatible medialib manager version 2.9.10 supporting several MPD player instances at the same time.

MediaLibManager supports various formats: flac, ape, wv, m4a, mp3, dsf. Also as single image CUE or multiple tracks CUE for flac,ape, wv.
Controls MPD instances via web interface on Smart TV, Laptop or Smart phone
![MediaLibManager](/data/MediaLibManager.png)

Runs on x86 platform with Debian 10 incl. docker, also possible with Raspberry Pi incl. docker
## Docker compose
Prerequisite: docker and docker-compose are installed

  docker-compose build -> builds Apache and application images

  docker-compose build --build-arg wsgi_bld_ver=$(date +%Y-%s) -> to retrive only the last code changes in wsgi service using date timestamp

  docker-compose build --build-arg medialib_bld_ver=$(date +%Y-%s) -> to retrive only the last code changes in medialib service using date timestamp

  docker-compose --env-file <path to docker-compose env file>  up -d -> starts complete project

  env config example:
    DEVICE="//192.168.1.99/NasShare"
    DRIVER_OPTIONS="username=<user_name>,password=<password>, <your SMB device connection options>"



## Direct access to config, log, shares, etc
config is placed in /var/lib/docker/volumes/medialibmanager_config

music DB in /var/lib/docker/volumes/medialibmanager_db

log DB in /var/lib/docker/volumes/medialibmanager_log

wsl installation:
https://dev.to/bowmanjd/install-docker-on-windows-wsl-without-docker-desktop-34m9
docker compose 




## Other Resources
Raspberry Pi: https://github.com/raspberrypi
RaspiOS: https://www.raspbian.org/RaspbianRepository
moodeaudio.org: http://moodeaudio.org
MPD player: http://www.musicpd.org
