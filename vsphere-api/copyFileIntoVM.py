from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
from utils import *

import atexit
import sys
import logging
from vsphere import VSphere

import re
import requests

from config import Config, Machine

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format='%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(message)s')

# Start program
if __name__ == "__main__":
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

    vm = get_obj(content, [vim.VirtualMachine], 'rhel7-a')
    tools_status = vm.guest.toolsStatus
    running_status = vm.guest.toolsRunningStatus

    logging.debug(' {hostname} VM Tools status: {status} {r}'.format(hostname=vm.name, status=str(tools_status), r=running_status))
    pm = content.guestOperationsManager.processManager
    creds = vim.vm.guest.NamePasswordAuthentication(username='root', password='xxx')
    ps = vim.vm.guest.ProcessManager.ProgramSpec(programPath='/bin/ls', arguments='-l')
    pid = pm.StartProgramInGuest(vm, creds, ps)

    vsphere = VSphere(
        host=config.hostname,
        user=config.username,
        password=config.password,
        port=443)
    vsphere.connect()

    with open('rhel7-a.nmcli') as x:
        f = x.readlines()
        #vsphere.upload_file_to_guest(vm, 'root', 'xxx', f, '/root/rhel7-a.nmcli')
        #vsphere.move_file_in_guest(vm, 'root', 'xxx', 'rhel7-a.nmcli', '/root/rhel7-a.nmcli', True)

        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        url = content.guestOperationsManager.fileManager.InitiateFileTransferToGuest(vm, creds, '/tmp/nmcli',
                                        file_attribute,
                                        len(f), True)
        url = re.sub(r"^https://\*:", "https://" + str('192.168.8.103') + ":", url)
        resp = requests.put(url, data=f, verify=False)
        if not resp.status_code == 200:
            print
            "Error while uploading file"
        else:
            print
            "Successfully uploaded file"
