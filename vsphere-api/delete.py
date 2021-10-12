#!/usr/bin/python3

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from utils import *

import atexit
import sys
import logging
import argparse

import dns.update
import dns.query
import dns.tsigkeyring

from config import Config, Machine, VsCreadential

import ssl


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


def dns_for_vm(machine):
    keyring = dns.tsigkeyring.from_text({
        "dynamic.vmware.haf.": "jn694IwJ9IP4i5yGtSdIZJTFeFpVEvK2wa78gHVX8PohLNBQVYQd+JyGNX8A3hju8WmsNVo1Oq58YS93HR4HIQ=="
    })

    logging.debug("DNS records:")
    for arecord in machine.addresses:        
        logging.debug(" {} ({})".format(arecord, machine.addresses[arecord]))        
        update = dns.update.Update(zone='prod.vmware.haf'
                                   , keyname='dynamic.vmware.haf.'
                                   , keyring=keyring
                                   , keyalgorithm=dns.tsig.HMAC_SHA512)

        ip = machine.addresses[arecord]
        if isinstance(ip, list):
            for i in ip:
                update.delete(i, 'A')
                response = dns.query.tcp(update, '192.168.8.200')
                logging.debug(" A   DNS update response: {}".format(response.rcode()))
        else:
            update.delete(arecord, 'A')
            response = dns.query.tcp(update, '192.168.8.200')
            logging.debug(" A   DNS update response: {}".format(response.rcode()))

            update.delete(arecord, 'TXT')
            response = dns.query.tcp(update, '192.168.8.200')
            logging.debug(" TXT DNS update response: {}".format(response.rcode()))


# Start program
if __name__ == "__main__":
    ssl._create_default_https_context = ssl._create_unverified_context

    logging.basicConfig(stream=sys.stdout,
                        level=logging.DEBUG,
                        format='%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(message)s')

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--file',
                       required=False,
                       action='store',
                       help='Config filename to process in .yaml format')

    group.add_argument('-i', '--inventory',
                       required=False,
                       action='store',
                       help='Config filename to process in ansible inventory format')

    args = parser.parse_args()

    # parse yaml file
    if args.file:
        c = Config.createFromYAML(args.file)
    else:
        c = Config.createFromInventory(args.inventory)
    
    # Config
    config = VsCreadential.load('.credentials.yaml')
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

    for machine in c.machines:
        delete_vm(service_instance=si, machine=machine)
        dns_for_vm(machine)
    if c.cluster:
        dns_for_vm(c.cluster)

