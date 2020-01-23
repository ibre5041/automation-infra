#!/bin/bash

ssh root@192.168.8.103 "mkdir -p /vmfs/volumes/Kingston890G/rhel7-c"

scp rhel7-c.vmx root@192.168.8.103:/vmfs/volumes/Kingston890G/rhel7-c/rhel7-c.vmx

ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-c/disk-a-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-c/disk-a.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-c/disk-b-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-c/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 30g -d thin /vmfs/volumes/Kingston890G/rhel7-c/disk-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 50g -d thin /vmfs/volumes/Kingston890G/rhel7-c/disk-b.vmdk"

ssh root@192.168.8.103 "vim-cmd solo/registervm /vmfs/volumes/Kingston890G/rhel7-c/rhel7-c.vmx"
