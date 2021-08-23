This directory simply contains mine home-lab configurations.

ESXi inner config configurations

 - 192.168.8.0/24 is home local network managed by home DHCP (pciNumber:192, virtual eth adapter:ens192)
 - 10.0.0.0/24 is internal ESXi network managed by DHCP running on kicklinux machine(pciNumber:224, virtual eth adapter:ens224)

Kickstart Linux VM configuration:
 - DHCP
 - FTP/TFTP
 - HTTP
 - DNS
 - Nexus (.rpm, Maven proxy)
 - ... etc
 
