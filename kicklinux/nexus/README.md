
Nexus:
 - download latest version of Nexus
 - unpack in into /opt

```shell
[root@kicklinux nexus]# ls -ld /opt/*
lrwxrwxrwx. 1 root root  15 Jun 16 15:29 /opt/nexus -> nexus-3.16.2-01
drwxr-xr-x. 9 root root 163 Jun 16 15:28 /opt/nexus-3.16.2-01
drwxr-xr-x. 3 root root  20 Jun 16 15:28 /opt/sonatype-work
```

 - Setup local Centos mirror on URL: http://192.168.8.200:8081/repository/Centos/
 
![Centos repository mirror](https://github.com/ibre5041/automation-infra/blob/master/kicklinux/nexus/Centos.repo.png)
