#!/usr/bin/python3

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from utils import *

import atexit
import sys
import logging
import argparse

from config import Config, Machine, VsCreadential

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(message)s')


def delete_vm(service_instance, machine):
    vm = get_obj(content, [vim.VirtualMachine], machine.nameVSphere)

    if not vm:
        logging.debug("{machine} not found.".format(machine=machine.nameVSphere))
        return

    if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
        task = vm.PowerOff()
        wait_for_tasks(service_instance, [task])
    if vm.runtime.powerState == vim.VirtualMachinePowerState.suspended:
        task = vm.PowerOn()
        wait_for_tasks(service_instance, [task])
        task = vm.PowerOff()
        wait_for_tasks(service_instance, [task])
    task = vm.Destroy_Task()
    wait_for_tasks(service_instance, [task])
    logging.debug("{machine} destroyed.".format(machine=machine.nameVSphere))

# Start program
if __name__ == "__main__":
    config = VsCreadential.load('.credentials.yaml')

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
                        required=False,
                        action='store',
                        help='Config filename to process', default='rhel7-a.yaml')

    args = parser.parse_args()

    # parse yaml file
    c = Config.createFromYAML(args.file)
    # Connect
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
        delete_vm(service_instance=si, machine=machine)

