
//----------------------------------
// podman 
//----------------------------------
********* https://www.techrepublic.com/article/enable-podman-sudoless-container-management
**** https://linuxconfig.org/getting-started-with-containers-via-podman-no-docker-daemon-required
https://opensource.com/article/22/1/run-containers-without-sudo-podman
***** details on modes https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md
namespaces https://www.youtube.com/watch?v=Ac2boGEz2ww

rootless steps:
1: check subuid & subgid 
2: namespaces   - if lower create /etc/sysctl.d/userns.conf 
3: networking support

systemctl status podman
systemctl --user 

ms@ms000:~$ cat /etc/subuid
ms:100000:65536
ms@ms000:~$ cat /etc/subgid
ms:100000:65536

//check inside container
ps -ef 
ps -ef n 
cat /proc/1/uid_map 
cat /etc/passwd 
lsns
lsns -t pid 

//update /etc/subuid or /etc/subgid
$ sudo usermod --add-subuids 200000-265536 --add-subgids 200000-265536 tux
user.max_user_namespaces = 256004

$ sysctl --all --pattern user_namespaces
$ cat /etc/passwd

//---- 
- Docker: /var/lib/docker
- Podman ( root ): /var/lib/containers
- Podman ( normal_user ): ~/.local/share/containers

ls /var/lib/containers
ls ~/.local/share/containers

That's plenty of namespaces, and it's probably what your distribution has set by default. If your distribution doesn't have that property or has it set very low, then you can create it by entering this text into the file /etc/sysctl.d/userns.conf:

user.max_user_namespaces=28633
Load that setting:

$ sudo sysctl -p /etc/sysctl.d/userns.conf

//----------------------------------
// main configuration files
//----------------------------------
The three main configuration files are 
  - containers.conf, 
  - storage.conf 
  - registries.conf. 

storage.conf
For storage.conf the order is 
	/etc/containers/storage.conf
	${XDG_CONFIG_HOME}/containers/storage.conf

registries
Registry configuration is read in this order
	/etc/containers/registries.conf
	/etc/containers/registries.d/*
	${XDG_CONFIG_HOME}/containers/registries.conf



