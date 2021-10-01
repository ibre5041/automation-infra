#!/usr/bin/python3

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from utils import *

import atexit
import sys
import logging
import argparse
import humanfriendly

from config import Config, VsCreadential

import ssl
import time
import utils
import socket
from add_shared_disk import add_data_disk, add_shared_disk
import requests

import urllib3
urllib3.disable_warnings()


def clone_vm(service_instance, machine, template_name, resource_pool=None):
    vm = get_obj(content, [vim.VirtualMachine], machine.nameVSphere)

    if vm:
        logging.debug("{machine} already exists.".format(machine=machine.nameVSphere))
        return

    template = get_obj(content, [vim.VirtualMachine], template_name)

    datacenter = get_obj(content, [vim.Datacenter], 'Datacenter')
    if machine.folder:
        destfolder = get_obj(content, [vim.Folder], machine.folder)
    else:
        destfolder = datacenter.vmFolder

    if machine.datastore:
        datastore = get_obj(content, [vim.Datastore], machine.datastore)
    else:
        datastore = get_obj(
            content, [vim.Datastore], template.datastore[0].info.name)

    # if None, get the first one
    cluster = get_obj(content, [vim.ClusterComputeResource], 'Datacenter')

    if resource_pool:
        resource_pool = get_obj(content, [vim.ResourcePool], resource_pool)
    elif cluster:
        resource_pool = cluster.resourcePool
    else:
        resource_pool = content.rootFolder.childEntity[0].hostFolder.childEntity[0].resourcePool



    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = resource_pool

    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = False
    clonespec.location.pool = resource_pool

    logging.debug("cloning template {template_name} into {hostname}...".format(hostname=machine.nameVSphere, template_name=template_name))
    task = template.Clone(folder=destfolder, name=machine.nameVSphere, spec=clonespec)
    utils.wait_for_tasks(service_instance, [task])
    logging.debug("{hostname} created as clone of {template_name}".format(hostname=machine.nameVSphere, template_name=template_name))

    vm = get_obj(content, [vim.VirtualMachine], machine.nameVSphere)
    spec = vim.vm.ConfigSpec()

    # "stolen" from: https://stackoverflow.com/questions/30765940/how-do-i-modify-an-existing-vm-templates-only-ethernet-adapters-ip-address-wit
    spec.numCPUs = machine.cpu
    spec.memoryMB = int(humanfriendly.parse_size(machine.ram, binary=True) / 1024 / 1024)    
    spec.cpuHotAddEnabled = True
    spec.memoryHotAddEnabled = True
    logging.debug("VM CPU: {cpu}".format(cpu=spec.numCPUs))
    logging.debug("VM RAM: {ram}".format(ram=spec.memoryMB))

    spec.extraConfig = []
    opt = vim.option.OptionValue()
    opt.key = 'guestinfo.hostname'
    opt.value = machine.name
    spec.extraConfig.append(opt)

    opt = vim.option.OptionValue()
    opt.key = 'guestinfo.dns'
    opt.value = '192.168.8.200'
    spec.extraConfig.append(opt)

    prod_ip = socket.gethostbyname("{host}.prod.vmware.haf".format(host=machine.name))
    opt = vim.option.OptionValue()
    opt.key = 'guestinfo.prod_ip'
    opt.value = prod_ip
    spec.extraConfig.append(opt)

    try:
        barn_ip = socket.gethostbyname("{host}.barn.vmware.haf".format(host=machine.name))
        opt = vim.option.OptionValue()
        opt.key = 'guestinfo.barn_ip'
        opt.value = barn_ip
        spec.extraConfig.append(opt)
    except Exception:
        None

    task = vm.ReconfigVM_Task(spec=spec)
    wait_for_tasks(service_instance, [task])

    devices = []
    for i, scsi_adapter in enumerate(machine.scsiAdapters):
        if i == 0:              # assume 1st SCSI adapter is created, when clonning already created VM
            continue
        #
        scsi_ctr = vim.vm.device.VirtualDeviceSpec()
        scsi_ctr.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        scsi_ctr.device = vim.vm.device.ParaVirtualSCSIController()
        scsi_ctr.device.deviceInfo = vim.Description()
        scsi_ctr.device.slotInfo = vim.vm.device.VirtualDevice.PciBusSlotInfo()
        scsi_ctr.device.slotInfo.pciSlotNumber = scsi_adapter['pciSlotNumber']
        # scsi_ctr.device.controllerKey = 100
        scsi_ctr.device.deviceInfo = vim.Description()
        scsi_ctr.device.deviceInfo.label = 'Shared SCSI'
        scsi_ctr.device.deviceInfo.label = 'BUS for Shared SCSI disks'
        scsi_ctr.device.unitNumber = 3
        scsi_ctr.device.busNumber = i
        scsi_ctr.device.hotAddRemove = True
        # 1st SCSI adapter for local disk, rest for shared ones
        scsi_ctr.device.sharedBus = vim.vm.device.VirtualSCSIController.Sharing.noSharing if i == 0 else vim.vm.device.VirtualSCSIController.Sharing.virtualSharing
        scsi_ctr.device.scsiCtlrUnitNumber = 7

        devices.append(scsi_ctr)

        spec = vim.vm.ConfigSpec()
        spec.deviceChange = devices
        
        task = vm.ReconfigVM_Task(spec=spec)
        wait_for_tasks(service_instance, [task])
        logging.debug('Added SCSI adapter: {i} pciSlotNumber: {pciSlotNumber}'.format(i=i, pciSlotNumber=scsi_ctr.device.slotInfo.pciSlotNumber))


    task = vm.ReconfigVM_Task(spec)
    utils.wait_for_tasks(service_instance, [task])
    logging.debug("{machine} reconfigured.".format(machine=machine.nameVSphere))

    machine_disk_specs = machine.disks
    for dev in vm.config.hardware.device:
        if hasattr(dev.backing, 'fileName'):
            logging.debug("Device label: {label}".format(label=dev.deviceInfo.label))
            #if dev.deviceInfo.label in vm_disk.keys():
            capacity_in_kb = dev.capacityInKB
            new_disk_kb = capacity_in_kb
            #new_disk_kb = 40 * 1024 * 1024
            if machine_disk_specs:                
                disk_spec = machine_disk_specs.pop(0)
                new_disk_kb = int(humanfriendly.parse_size(disk_spec['size'], binary=True) / 1024 )
            if (capacity_in_kb != new_disk_kb):
                logging.debug("Device label: {label} new disk size: {size} MB".format(label=dev.deviceInfo.label, size=int(new_disk_kb/1024)))
            if new_disk_kb > capacity_in_kb:
                dev_changes = []
                disk_spec = vim.vm.device.VirtualDeviceSpec()
                disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                disk_spec.device = vim.vm.device.VirtualDisk()
                disk_spec.device.key = dev.key
                disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
                disk_spec.device.backing.fileName = dev.backing.fileName
                disk_spec.device.backing.diskMode = dev.backing.diskMode
                disk_spec.device.controllerKey = dev.controllerKey
                disk_spec.device.unitNumber = dev.unitNumber
                disk_spec.device.capacityInKB = new_disk_kb
                dev_changes.append(disk_spec)

                spec = vim.vm.ConfigSpec()
                spec.deviceChange = dev_changes

                task = vm.ReconfigVM_Task(spec=spec)
                wait_for_tasks(service_instance, [task])

    spec = vim.vm.ConfigSpec()
    for dev in vm.config.hardware.device:
        if hasattr(dev, 'macAddress'):
            vm_slot_number = dev.slotInfo.pciSlotNumber
            adapter = next(a for a in machine.netAdapters if a['pciSlotNumber'] == vm_slot_number)
            net_adapter_spec = vim.vm.device.VirtualDeviceSpec()
            net_adapter_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            net_adapter_spec.device = dev
            if adapter:
                net_adapter_spec.device.addressType = "generated"
                net_adapter_spec.device.macAddress = adapter['mac']
                net_adapter_spec.device.macAddress = None
                spec.deviceChange.append(net_adapter_spec)
                logging.debug('Net Adapter PCI: {} assigning new MAC Address: {}'.format(vm_slot_number, dev.macAddress))
            try:    
                net = get_obj(content, [vim.Network], adapter['network'])
                net_adapter_spec.device.backing.network = net
                net_adapter_spec.device.backing.deviceName = net.name
                logging.debug('Net Adapter PCI: {} assigning new network: {}'.format(vm_slot_number, net.name))
            except Exception as e:
                logging.warn('Net Adapter PCI: {}'.format(str(e)))

    task = vm.ReconfigVM_Task(spec=spec)
    wait_for_tasks(service_instance, [task])

    task = vm.PowerOn()
    wait_for_tasks(service_instance, [task])
    logging.debug("{machine} booting...".format(machine=machine.nameVSphere))
    logging.debug("Waiting for vmware tools...")

    for i in range(1,60):
        time.sleep(1)
        vm = get_obj(content, [vim.VirtualMachine], machine.nameVSphere)
        _columns_four = "{0!s:<20} {1!s:<20}/{3!s:<20} {2!s:<30}"
        logging.debug(_columns_four.format(vm.name,
                                        vm.guest.toolsRunningStatus,
                                        vm.guest.toolsVersionStatus2,
                                        vm.guest.toolsVersion))
        if vm.guest.toolsRunningStatus == 'guestToolsRunning':
            break

    logging.debug("Executing mncli :")
    creds = vim.vm.guest.NamePasswordAuthentication(username='root', password='kolikmn')
    pm = service_instance.content.guestOperationsManager.processManager
    ps = vim.vm.guest.ProcessManager.ProgramSpec(programPath='/usr/bin/nmcli', arguments='con show  &> sample.txt')
    res = pm.StartProgramInGuest(vm, creds, ps)

    src = "/root/sample.txt"  # Server's directory
    fti = content.guestOperationsManager.fileManager.InitiateFileTransferFromGuest(vm, creds, src)
    resp = requests.get(fti.url, verify=False)
    logging.debug("Content: {}".format(resp.content))

# Start program
if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
                        required=False,
                        action='store',
                        help='Config filename to process', default='rhel7-a.yaml')

    args = parser.parse_args()

    # parse yaml file
    c = Config.createFromYAML(args.file)
    # Connect
    config = VsCreadential.load('.credentials.yaml')
    #
    si = SmartConnect(
        host=config.hostname,
        user=config.username,
        pwd=config.password,
        port=443)
    # disconnect this thing
    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    c.validate(content)

    for machine in c.machines:
        clone_vm(service_instance=si, machine=machine, template_name=(machine.template or 'RHEL8 Template'))
        for disk in machine.disks:
            if disk['bus'] == 0:
                continue
            add_data_disk(service_instance=si, machine=machine, disk=disk)

    if c.cluster:
        add_shared_disk(service_instance=si, config=c)
