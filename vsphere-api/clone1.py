import requests
import urllib3

from six.moves import cStringIO

from com.vmware.vcenter.vm.hardware.boot_client import Device as BootDevice
from com.vmware.vcenter.vm.hardware_client import (Cpu, Memory, Disk, Ethernet, Cdrom, Serial, Parallel, Floppy, Boot)
from com.vmware.vcenter.vm_client import (Hardware, Power)
from com.vmware.vcenter_client import VM, Network, Folder
from vmware.vapi.bindings.struct import PrettyPrinter

from vmware.vapi.vsphere.client import create_vsphere_client
from com.vmware.vcenter_client import Datacenter, Host, Datastore

from com.vmware.vcenter.vm.hardware.adapter_client import Scsi
from com.vmware.vcenter.vm.hardware_client import ScsiAddressSpec

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

rac1_vm = client.vcenter.VM.list(VM.FilterSpec(names=set(['RAC1'])))[0]
rac1_vm_info = client.vcenter.VM.get(rac1_vm.vm)
print(rac1_vm_info)
scsi_summaries = client.vcenter.vm.hardware.adapter.Scsi.list(vm=rac1_vm.vm)

for s in scsi_summaries:
    x = client.vcenter.vm.hardware.adapter.Scsi.get(vm=rac1_vm.vm, adapter=s.adapter)
    print(x)

GiB = 1024 * 1024 * 1024
GiBMemory = 1024

def pp(value):
    """ Utility method used to print the data nicely. """
    output = cStringIO()
    PrettyPrinter(stream=output).pprint(value)
    return output.getvalue()

filter_spec = Datacenter.FilterSpec(names=set(['Datacenter']))
datacenter_summaries = client.vcenter.Datacenter.list(filter_spec)
datacenter = datacenter_summaries[0].datacenter

filter_spec = Folder.FilterSpec(names=set(['VmFolder'])
                                #, datacenters=set(['Datacenter'])
                                )
folder_summaries = client.vcenter.Folder.list(filter_spec)
folder = folder_summaries[0].folder
print(folder)

filter_spec = Host.FilterSpec(names=set(['esxi-1.prod.vmware.haf']))
host_summaries = client.vcenter.Host.list(filter_spec)
host = host_summaries[0]
print(host)

filter_spec = Datastore.FilterSpec(names=set(['Kingston120G']))
datastore_summaries = client.vcenter.Datastore.list(filter_spec)
datastore = datastore_summaries[0]
print(datastore)

filter_spec = Network.FilterSpec(#datacenters=set(['Datacenter']),
                                 names=set(['VM Network']),
                                 types=set([Network.Type.STANDARD_PORTGROUP])
                                 )
network_summaries = client.vcenter.Network.list(filter=filter_spec)
print(network_summaries)
network_summaries = client.vcenter.Network.list()
network1 = network_summaries[0]
print(network1)
network2 = network_summaries[1]
print(network2)


placement_spec = VM.PlacementSpec(folder=folder,
    #resource_pool=resource_pool,
    #host='esxi-1.prod.vmware.haf',
    host=host.host,
    datastore=datastore.datastore)

scsi_create_spec0 = Scsi.CreateSpec(bus=0, pci_slot_number=160, sharing=Scsi.Sharing.NONE)
scsi_create_spec1 = Scsi.CreateSpec(bus=1, pci_slot_number=256, sharing=Scsi.Sharing.PHYSICAL)
#scsi_create_spec2 = Scsi.CreateSpec(bus=2, pci_slot_number=256, sharing=Scsi.Sharing.PHYSICAL)

disk_create_spec0 = Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                    scsi=ScsiAddressSpec(bus=0, unit=0),
                                    new_vmdk=Disk.VmdkCreateSpec(name='disk-0', capacity=10 * GiB))
disk_create_spec1 = Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                    scsi=ScsiAddressSpec(bus=0, unit=1),
                                    new_vmdk=Disk.VmdkCreateSpec(name='disk-1', capacity=10 * GiB))

disk_create_spec2 = Disk.CreateSpec(type=Disk.HostBusAdapterType.SCSI,
                                    scsi=ScsiAddressSpec(bus=2, unit=0),
                                    new_vmdk=Disk.VmdkCreateSpec(name='disk-shared-0', capacity=4 * GiB))

#[Kingston120G] SHARED/RAC_SSD_1.vm

vm_create_spec = VM.CreateSpec(
    guest_os='CENTOS_7_64',
    name='TESTVM',
    placement=placement_spec,
    hardware_version=Hardware.Version.VMX_13,
    cpu=Cpu.UpdateSpec(count=2, cores_per_socket=1, hot_add_enabled=False, hot_remove_enabled=False),
    memory=Memory.UpdateSpec(size_mib=2 * GiBMemory, hot_add_enabled=False),
    boot=Boot.CreateSpec(type=Boot.Type.BIOS, delay=0, enter_setup_mode=False),
    boot_devices=[
        BootDevice.EntryCreateSpec(BootDevice.Type.DISK),
        BootDevice.EntryCreateSpec(BootDevice.Type.ETHERNET)
    ],
    nics=[
        Ethernet.CreateSpec(
            start_connected=True,
            mac_type=Ethernet.MacAddressType.MANUAL,
            mac_address='11:23:58:13:21:34',
            pci_slot_number=192,
            backing=Ethernet.BackingSpec(type=Ethernet.BackingType.STANDARD_PORTGROUP, network=network1.network)
        )
    ],
    scsi_adapters=[scsi_create_spec0, scsi_create_spec1],
    disks=[disk_create_spec0, disk_create_spec1]
)


vm = client.vcenter.VM.create(vm_create_spec)
print("create_exhaustive_vm: Created VM '{}' ({})".format(vm_create_spec.name, vm))
