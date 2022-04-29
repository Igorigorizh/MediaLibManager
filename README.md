# MediaLibManager
Linux compatible medialib manager version 2.9.10 supporting several MPD player instances at the same time.

Runs on x86 platform with Debian 10 incl. docker , also possible with Raspberry Pi incl. docker
## Docker compose
docker-compose build -> builds Apache and application images

docker-compose build --build-arg medialib_bld_ver=$(date +%Y-%s)  --build-arg wsgi_bld_ver=$(date +%Y-%s) -> to retrive only the last code changes wsgi+medialib using date timestamp

docker-compose build --build-arg medialib_bld_ver=$(date +%Y-%s) -> to retrive only the last code changes in medialib using date timestamp

docker-compose up -d -> starts complete project
## Direct access to config, log, shares, etc
config is placed in /var/lib/docker/volumes/medialibmanager_config

music DB in /var/lib/docker/volumes/medialibmanager_db

log DB in /var/lib/docker/volumes/medialibmanager_log

## Other Resources
Raspberry Pi: https://github.com/raspberrypi
RaspiOS: https://www.raspbian.org/RaspbianRepository
moodeaudio.org: http://moodeaudio.org
MPD player: http://www.musicpd.org
