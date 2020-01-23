#!/bin/bash

ssh root@192.168.8.103 "mkdir -p /vmfs/volumes/Kingston890G/rhel7-b"

scp rhel7-b.vmx root@192.168.8.103:/vmfs/volumes/Kingston890G/rhel7-b/rhel7-b.vmx

ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-b/disk-a-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-b/disk-a.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-b/disk-b-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-b/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 30g -d thin /vmfs/volumes/Kingston890G/rhel7-b/disk-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 50g -d thin /vmfs/volumes/Kingston890G/rhel7-b/disk-b.vmdk"

ssh root@192.168.8.103 "vim-cmd solo/registervm /vmfs/volumes/Kingston890G/rhel7-b/rhel7-b.vmx"
