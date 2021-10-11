## RAC on ESXi home lab

This repository is just a sandbox for Oracle RAC oriented tests.
I use pyvmomi to create/update/delete VMs, ansible to install various testing environments.
Altough ansible supports VCenter API, not all necessary functionality is implemented.

# kicklinux jump-host
Whole home lab net is managed from kicklinux VM (See kicklinux directory for more details)
This VM serves as:
 - DNS
 - DHCP
 - TFTP (PXE, anaconda install)
 - Nexus .rpm proxy
 - HTTP/FTP


# VM creation
vsphere-api directory:
 - config.py, utilitty class for parsing .yaml config files (VM hw definition)
 - create.py, create plain empty VM hw, use kicklinux/anaconda to install OS (RHEL7/RHEL8) on such a VM. Convert it into VM Template then.
 - clone.py, clone VM Template into live VM (including IP setup, and DDNS registration)
 - delete.py, decomm VM

# VM's HW definition
- Oracle node has 2x NIC adapters(prod + barn/interconnect), 2x SCSI adapter( OS/APP DG + DATA disks)


.yaml config file:

    scsi:
      - adapter:
          pciSlotNumber: 16
      - adapter:
          pciSlotNumber: 32
    disks:
      ... ( omited)
    network:
      - adapter:
        pciSlotNumber: 192
        network: "Public Network"
      - adapter:
        pciSlotNumber: 224
        network: "Barn Network"

    # lspci
    03:00.0 Serial Attached SCSI controller: VMware PVSCSI SCSI Controller (rev 02)
    0b:00.0 Ethernet controller: VMware VMXNET3 Ethernet Controller (rev 01) 
    13:00.0 Ethernet controller: VMware VMXNET3 Ethernet Controller (rev 01)
    1b:00.0 Serial Attached SCSI controller: VMware PVSCSI SCSI Controller (rev 02)

- 1st SCSI adapter pciSlotNumber(16) has two disks on it (vg00 Centos OS, vg01 applications instalation)
- 2nd SCSI adapter pciSlotNumber(32) - when present - contains shared SCSI disk, intended for RAC data (ASM disk group)

- 1st NIC adapter pciSlotNumber(192) is connected to ESXi's Network "Public Network" 192.168.8.0/24
- 2st NIC adapter pciSlotNumber(224) is connected to ESXi's Network "Barn Network" 10.0.0.0/24, this is also interface there DHCP,TFTP listens on
