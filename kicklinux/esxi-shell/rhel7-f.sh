#!/bin/bash

ssh root@192.168.8.103 "mkdir -p /vmfs/volumes/Kingston890G/rhel7-f"

scp rhel7-f.vmx root@192.168.8.103:/vmfs/volumes/Kingston890G/rhel7-f/rhel7-f.vmx

ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-f/disk-a-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-f/disk-a.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-f/disk-b-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/rhel7-f/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 30g -d thin /vmfs/volumes/Kingston890G/rhel7-f/disk-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 50g -d thin /vmfs/volumes/Kingston890G/rhel7-f/disk-b.vmdk"

ssh root@192.168.8.103 "vim-cmd solo/registervm /vmfs/volumes/Kingston890G/rhel7-f/rhel7-f.vmx"
