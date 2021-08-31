# MediaLibManager
new linux compatible medialib manager version
igor@W-PF221L6E:~$ sudo mount -t cifs -o "username=$(>&2 echo -n "Enter remote username: "; read u; echo $u),uid=$(id -u),gid=$(id -g)" //192.168.1.67/ExternalUSB /mnt/GoflexHomeUSB