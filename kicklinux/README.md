# kicklinux
This directory simply contains mine home-lab configurations.
kicklinux is management jump-host VM (IP: 192.168.8.200, 10.0.0.200)

ESXi inner config configurations

 - `192.168.8.0/24` is home local network managed by home DHCP (pciNumber:192, virtual eth adapter:ens192) "Public Network"
 - `10.0.0.0/24` is internal ESXi network managed by DHCP running on kicklinux machine(pciNumber:224, virtual eth adapter:ens224) "Barn Network". This one it not routed

Kickstart Linux VM configuration:
 - DHCP
 
 DHCP server assigns IPs on "Barn Network", supports PXE boot options. 
 VMs are created with convention, where last two bytes of MAC address correspond to last byte of IP:
 
 `host dhcp-192-168-8-104      { hardware ethernet 00:50:56:00:01:04; fixed-address 10.0.0.104     ; }`

 DHCP config is managed via this git repository:
 
    [root@kicklinux dhcp]# ls -l /etc/dhcp/dhcpd.conf
    lrwxrwxrwx. 1 root root 52 Oct 20  2019 /etc/dhcp/dhcpd.conf -> /root/automation-infra/kicklinux/etc.dhcp.dhcpd.conf

 - FTP
 
 vsftp config is managed via this repositoty (but actually ftp is not used at all, http is mostly used).
 vsftp is used as TFTP server (`anon_root=/var/lib/tftpboot/images`).
 
    [root@kicklinux vsftpd]# ls -l /etc/vsftpd/vsftpd.conf
    lrwxrwxrwx. 1 root root 55 Oct 20  2019 /etc/vsftpd/vsftpd.conf -> /root/automation-infra/kicklinux/etc.vsftpd.vsftpd.conf
 
 Note: TFTP does not support symlinks
 
    [root@kicklinux tftpboot]# pwd
    /var/lib/tftpboot
    [root@kicklinux tftpboot]# ls -l
    total 185220
    -rw-r--r--. 1 root root    20704 Jul  2  2017 chain.c32
    drwxr-xr-x. 3 root root       40 Oct 20  2019 images
    -rw-r--r--. 1 root root 52893200 May  3  2018 initrd7.img
    -rw-r--r--. 1 root root 75378504 Aug 23 16:01 initrd8.img
    -r--r--r--. 1 root root 40688737 Jul  2  2017 initrd.img
    -rw-r--r--. 1 root root    33628 Jul  2  2017 mboot.c32
    -rw-r--r--. 1 root root    26140 Jul  2  2017 memdisk
    -rw-r--r--. 1 root root    55012 Jul  2  2017 menu.c32
    -rw-r--r--. 1 root root    26764 Jul  2  2017 pxelinux.0
    drwxr-xr-x. 2 root root     4096 Aug 23 20:06 pxelinux.cfg
    -r-xr-xr-x. 1 root root  4264528 Jul  2  2017 vmlinuz
    -rwxr-xr-x. 1 root root  6224704 Apr 20  2018 vmlinuz7
    -rwxr-xr-x. 1 root root 10026120 Aug 23 16:00 vmlinuz8

  Directory `pxelinux.cfg` contains PXE config files. File matches VM's MAC in arbitrary format:
  
    [root@kicklinux tftpboot]# ls -lr pxelinux.cfg/
    total 92
    -rw-r--r--. 1 root root 379 Aug 23 16:02 default
    -rw-r--r--. 2 root root 270 Jul 13  2019 01-00-50-56-00-02-54
    -rw-r--r--. 2 root root 270 Jul 13  2019 01-00-50-56-00-02-53
    -rw-r--r--. 2 root root 270 Jul 13  2019 01-00-50-56-00-02-52
     
    [root@kicklinux tftpboot]# cat pxelinux.cfg/default 
    DEFAULT menu.c32
    PROMPT 0
    TIMEOUT 60
    ONTIMEOUT CentOS7
    
    MENU TITLE PXE Menu
    
    LABEL CentOS7
    KERNEL vmlinuz7
    APPEND initrd=initrd7.img inst.ks=http://10.0.0.200/centos/rhel7-ks.cfg id=dhcp
    
    LABEL CentOS8
    KERNEL vmlinuz8
    APPEND initrd=initrd8.img inst.ks=http://10.0.0.200/centos/rhel8-ks.cfg id=dhcp
    
    #MENU seperator
    LABEL Local
    LOCALBOOT 0Here two things which you need to change
    [root@kicklinux tftpboot]# 
    [root@kicklinux tftpboot]# 
    [root@kicklinux tftpboot]# 
    [root@kicklinux tftpboot]# cat pxelinux.cfg/01-00-50-56-00-02-54
    DEFAULT menu.c32
    PROMPT 0
    TIMEOUT 60
    ONTIMEOUT CentOS7
    
    MENU TITLE PXE Menu
    
    LABEL CentOS7
    KERNEL vmlinuz7
    APPEND initrd=initrd7.img inst.ks=http://10.0.0.200/centos/rhel7-e-ks.cfg id=dhcp
    
    #MENU seperator
    LABEL Local
    LOCALBOOT 0Here two things which you need to change
 
 Sub-directory images contains anaconda/kickstart config files, plus Centos base OS installation media.
 But those are served over HTTP.
 
    [root@kicklinux tftpboot]# ls -l images/
    total 8
    drwxr-xr-x. 5 root root 4096 Aug 23 22:06 centos
    -rw-------. 1 root root 1387 Jul  2  2017 ks-rhel7.cfg
    [root@kicklinux tftpboot]# ls -l images/centos/
    total 108
    drwxr-xr-x. 3 root root   20 Jul  2  2017 6
    drwxr-xr-x. 3 root root   20 Jun 16  2019 7
    drwxr-xr-x. 3 root root   20 Aug 23 15:55 8
    -rw-r--r--. 2 root root 2053 Jul  2  2017 rhel6-ks.cfg
    -rw-r--r--. 2 root root 4051 Jan 25  2020 rhel7-a-ks.cfg
    -rw-r--r--. 2 root root 4052 Oct 20  2019 rhel7-b-ks.cfg
    -rw-r--r--. 2 root root 3441 Jul 20  2019 rhel7-ceph1-ks.cfg

 - HTTP is used for:
 
   - anaconda-ks/kickstart unattended Linux installation
   - yum repository
   - HTTP source of binaries used by ansible 
 
 HTTP config managed via this git repository:
 
     [root@kicklinux conf]# pwd
     /etc/httpd/conf
     [root@kicklinux conf]# ls -l httpd.conf
     lrwxrwxrwx. 1 root root 58 Oct 20  2019 httpd.conf -> /root/automation-infra/kicklinux/etc.httpd.conf.httpd.conf

 - DNS

Bind resolves IPs in both VLANs. Also supports DDNS, so when a new VM is provisioned is is also registered in DNS.

DNS config managed via this git repository:

    [root@kicklinux etc]# pwd
    /etc
    [root@kicklinux etc]# ls -l /etc/named.conf /etc/named
    lrwxrwxrwx. 1 root root 42 Oct 20  2019 /etc/named -> /root/automation-infra/kicklinux/etc.named
    lrwxrwxrwx. 1 root root 47 Oct 20  2019 /etc/named.conf -> /root/automation-infra/kicklinux/etc.named.conf

 - Nexus (.rpm, Maven proxy)
 - ... etc
 
