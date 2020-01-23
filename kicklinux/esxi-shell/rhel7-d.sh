#!/bin/bash

ssh root@192.168.8.103 "mkdir -p /vmfs/volumes/Kingston890G/rhel7-d"

scp rhel7-d.vmx root@192.168.8.103:/vmfs/volumes/Kingston890G/rhel7-d/rhel7-d.vmx

ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-d/disk-a-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-d/disk-a.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-d/disk-b-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-d/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 30g -d thin /vmfs/volumes/Kingston890G/rhel7-d/disk-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 50g -d thin /vmfs/volumes/Kingston890G/rhel7-d/disk-b.vmdk"

ssh root@192.168.8.103 "vim-cmd solo/registervm /vmfs/volumes/Kingston890G/rhel7-d/rhel7-d.vmx"
