# kicklinux
This directory simply contains mine home-lab configurations.

ESXi inner config configurations

 - 192.168.8.0/24 is home local network managed by home DHCP (pciNumber:192, virtual eth adapter:ens192) "Public Network"
 - 10.0.0.0/24 is internal ESXi network managed by DHCP running on kicklinux machine(pciNumber:224, virtual eth adapter:ens224) "Barn Network". this one it not routed

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
 Note: TFTP does not support symlinks
 
    [root@kicklinux vsftpd]# ls -l /etc/vsftpd/vsftpd.conf
    lrwxrwxrwx. 1 root root 55 Oct 20  2019 /etc/vsftpd/vsftpd.conf -> /root/automation-infra/kicklinux/etc.vsftpd.vsftpd.conf
 
 - HTTP
 - DNS
 - Nexus (.rpm, Maven proxy)
 - ... etc
 
