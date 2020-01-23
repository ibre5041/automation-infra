import requests
import urllib3

from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (Cpu, Memory, Disk, Ethernet, Cdrom, Serial, Parallel, Floppy, Boot)
from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec
from com.vmware.vcenter.vm_client import (Hardware, Power)
from com.vmware.vcenter_client import VM, Network

from com.vmware.vcenter_client import Datacenter, Host, ResourcePool
from vmware.vapi.vsphere.client import create_vsphere_client

#from pyVmomi import vim, vmodl


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

context = None # get_unverified_context

filter_spec = Datacenter.FilterSpec(names=set(['Datacenter']))
datacenter_summaries = client.vcenter.Datacenter.list(filter_spec)
datacenter = datacenter_summaries[0].datacenter

filter_spec = Host.FilterSpec(names=set(['esxi-1.prod.vmware.haf']))
host_summaries = client.vcenter.Host.list(filter_spec)
host = host_summaries[0].host

print(client.vcenter.Host.list())



# List all VMs inside the vCenter Server
for vm in client.vcenter.VM.list():
    print(vm)
    VM = client.vcenter.VM.get(vm.vm)
    #print(VM)
    print(type(VM))

