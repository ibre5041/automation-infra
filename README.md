# vsphere-rac

  Vshere RAC

This repository is just a sandbox for Oracle RAC oriented test.
I use pyvmomi to create/update/delete VMs

VM specification:
- 2x NIC (Interconnect and PROD)

  network:
    - adapter:
        pciSlotNumber: 192
        network: "VM network inerconnect"
    - adapter:
        pciSlotNumber: 224
        network: "VM Network"

- 2x SCSI (one for rootdg+appdg, other for data disks)

  scsi:
    - adapter:
        pciSlotNumber: 128
    - adapter:
        pciSlotNumber: 128
