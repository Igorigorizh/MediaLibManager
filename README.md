# MediaLibManager
Linux compatible medialib manager version 2.9.7 supporting several MPD player instances at the same time.

Runs on x86 platform with Debian 10 incl. docker , also possible with Raspberry Pi incl. docker
## Docker compose
docker-compose build -> builds Apache and application images
docker-compose build --build-arg CACHE_VER="8" -> to retrive only the last code changes (increment CACHE_VER at every build)

docker-compose up -> starts complete project
### Pure Dockerfiles starting scenario
#### Doker image start 1: Apache instance via Dockerfile 
docker run -it - detach -p 80:80 --rm apacheImageID
#### Doker image start 2: app instance via Dockerfile
docker run -it -p 6600:6600 -p 9001:9001  --rm appimageID

## Other Resources
Raspberry Pi: https://github.com/raspberrypi
RaspiOS: https://www.raspbian.org/RaspbianRepository
moodeaudio.org: http://moodeaudio.org
MPD player: http://www.musicpd.org
