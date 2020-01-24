from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from utils import *

import atexit
import sys
import logging

from config import Config, VsCreadential

import ssl

import utils
import socket
from add_shared_disk import add_data_disk, add_shared_disk


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

    vm = vim.vm.ConfigSpec()
    # "stolen" from: https://stackoverflow.com/questions/30765940/how-do-i-modify-an-existing-vm-templates-only-ethernet-adapters-ip-address-wit
    vm.numCPUs = machine.cpu
    # vm.memoryMB = deploy_settings['mem']
    vm.cpuHotAddEnabled = True
    vm.memoryHotAddEnabled = True

    task = template.Clone(folder=destfolder, name=machine.nameVSphere, spec=clonespec)
    utils.wait_for_tasks(service_instance, [task])
    logging.debug("{hostname} crated as clone of {template_name}".format(hostname=machine.nameVSphere, template_name=template_name))

    vm = get_obj(content, [vim.VirtualMachine], machine.nameVSphere)
    spec = vim.vm.ConfigSpec()
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

    task = vm.ReconfigVM_Task(spec)
    utils.wait_for_tasks(service_instance, [task])
    logging.debug("{machine} reconfigured.".format(machine=machine.nameVSphere))

    task = vm.PowerOn()
    wait_for_tasks(service_instance, [task])
    logging.debug("{machine} booting.".format(machine=machine.nameVSphere))


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

    #sys.exit(0)

    for machine in c.machines:
        clone_vm(service_instance=si, machine=machine, template_name='RHEL7 Template')
        for disk in machine.disks:
            if disk['bus'] == 0:
                continue
            add_data_disk(service_instance=si, machine=machine, disk=disk)

    if c.cluster:
        add_shared_disk(service_instance=si, config=c)
