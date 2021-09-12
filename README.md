# MediaLibManager
Linux compatible medialib manager version 2.9.7 supporting several MPD player instances at the same time

# Doker image start 1: Apache instance
docker run -it - detach -p 80:80 --rm apacheImageID
# Doker image start 2: app instance
docker run -it -p 6600:6600 -p 9001:9001  --rm appimageID

# Mount command
mount -t cifs -o username=igor,vers=1.0 //192.168.1.67/ExternalUSB /mnt/GoflexHome/
