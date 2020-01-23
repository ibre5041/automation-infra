#!/bin/bash

HOSTNAME=rhel7-ora-c

ssh root@192.168.8.103 "mkdir -p /vmfs/volumes/Kingston890G/${HOSTNAME}"

scp ${HOSTNAME}.vmx root@192.168.8.103:/vmfs/volumes/Kingston890G/${HOSTNAME}/${HOSTNAME}.vmx

ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-a-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-a.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-b-flat.vmdk"
ssh root@192.168.8.103 "rm -f /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 30g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 50g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/disk-b.vmdk"

ssh root@192.168.8.103 "vmkfstools -c 8g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/data-a.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 8g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/data-b.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 8g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/data-c.vmdk"
ssh root@192.168.8.103 "vmkfstools -c 8g -d thin /vmfs/volumes/Kingston890G/${HOSTNAME}/data-d.vmdk"

ssh root@192.168.8.103 "vim-cmd solo/registervm /vmfs/volumes/Kingston890G/${HOSTNAME}/${HOSTNAME}.vmx"
