# MediaLibManager
Linux compatible medialib manager version 2.9.7 supporting several MPD player instances at the same time
## Docker compose
docker-compose build -> builds Apache and application images

docker-compose up - starting complete project
## Pure Dockerfiles strart scenario
### Doker image start 1: Apache instance via Dockerfile 
docker run -it - detach -p 80:80 --rm apacheImageID
### Doker image start 2: app instance via Dockerfile
docker run -it -p 6600:6600 -p 9001:9001  --rm appimageID

## Mount command
mount -t cifs -o username=igor,vers=1.0 //192.168.1.67/ExternalUSB /mnt/GoflexHome/
