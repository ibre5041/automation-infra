import requests
import urllib3

from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (Cpu, Memory, Disk, Ethernet, Cdrom, Serial, Parallel, Floppy, Boot)
from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec
from com.vmware.vcenter.vm_client import (Hardware, Power)
from com.vmware.vcenter_client import VM, Network, Folder
from vmware.vapi.bindings.struct import PrettyPrinter

from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import Datacenter, Host, Datastore

from com.vmware.vcenter.vm.hardware_client import Ethernet

session = requests.session()

# Disable cert verification for demo purpose.
# This is not recommended in a production environment.
session.verify = False

# Disable the secure connection warning for demo purpose.
# This is not recommended in a production environment.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Connect to a vCenter Server using username and password
config = VsCreadential.load('.credentials.yaml')
client = create_vsphere_client(server=config.hostname, username=config.username, password=config.password, session=session)

vm = 'TESTVM'

vm = client.vcenter.VM.list(VM.FilterSpec(names=set(['TESTVM'])))[0]
vm_info = client.vcenter.VM.get(vm.vm)

print('vm.get({}) -> {}'.format(vm, vm_info))

state = client.vcenter.vm.Power.get(vm.vm)
if state == Power.Info(state=Power.State.POWERED_ON):
    client.vcenter.vm.Power.stop(vm.vm)
elif state == Power.Info(state=Power.State.SUSPENDED):
    client.vcenter.vm.Power.start(vm.vm)
    client.vcenter.vm.Power.stop(vm.vm)
client.vcenter.VM.delete(vm.vm)
print("Deleted VM -- '{}-({})".format('TESTVM', vm.vm))
