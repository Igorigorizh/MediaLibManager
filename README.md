# MediaLibManager
new linux compatible medialib manager version

# Doker image start 1: Apache instance
docker run -it - detach -p 80:80 --rm apacheImageID
# Doker image start 2: app instance
docker run -it -p 80:80 -p 9001:9001 -p 6600:6600 --rm imageID

# Mount command
igor@myhost:~$ sudo mount -t cifs -o "username=$(>&2 echo -n "Enter remote username: "; read u; echo $u),uid=$(id -u),gid=$(id -g)" //192.168.1.67/ExternalUSB /mnt/GoflexHomeUSB
#Docker KB
https://habr.com/ru/company/otus/blog/512404/
