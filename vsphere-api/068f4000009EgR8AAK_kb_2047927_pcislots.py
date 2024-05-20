#! /usr/bin/python

import re

class VMHardware(object):

  def __init__(self):
     self.dev2slot = {}

  def add(self, dev, slot):
     if self.dev2slot.get(dev, None) != None:
        raise RuntimeError('%s device name is not unique' % (dev))
     if slot == -1:
        raise RuntimeError('%s comes from old virtual hardware' % (dev))
     self.dev2slot[dev] = slot

  def getKnownDevices(self):
     return self.dev2slot.keys()

  def getGuestPCIPath(self, dev):
     path = ''
     function = 0
     while True:
        slot = self.dev2slot.get(dev)
        if slot == None:
            raise RuntimeError('%s does not exist' % (dev))
        if slot == -1:
            raise RuntimeError('%s is legacy device' % (dev))
        bus = slot >> 5
        devNum = slot & 0x1F
        bridgeNr = bus & 0x1F
        if bridgeNr == 0:
            if bus != 0:
               raise RuntimeError('%s uses invalid slot' % (dev))
            break
        path = '[x]--%02X.%X' % (devNum, function) + path
        function = bus >> 5
        if function >= 8:
            raise RuntimeError('Device %s has unknown parent bridge' % (dev))
        dev = 'pcibridge%u' % (bridgeNr - 1)
     path = '%02X.%X--' % (devNum, function) + path
     return '[0000:00]-+-' + path

def LoadVMConfig(fileName):
  hardware = VMHardware()
  keyval = {}
  f = open(fileName, 'r')
  while True:
     line = f.readline()
     if line == '':
        break
     # We ignore '#' in quotes.  They are illegal for pciSlotNumber and present keys
     m = re.match(r'^([^#]*)#', line)
     if m != None:
        line = m.group(1)
     m = re.match(r'^([^=]*)=(.*)', line)
     if m == None:
        continue
     key = m.group(1).strip()
     value = m.group(2).strip()
     # We ignore escapes
     if len(value) > 1 and value[0] == '"':
        value = value[1:-1]
     keyval[key.lower()] = value
  for key in keyval.keys():
     m = re.match(r'^([^.]*)\.pcislotnumber', key)
     if m != None:
        pres = keyval.get('%s.present' % (m.group(1)))
        if pres != None and (pres[0].lower() == 't' or pres[0].lower() == 'y' or pres[0] == '1'):
           try:
              slot = int(keyval[key])
           except:
              print("Ignoring %s: %s is not valid slot number" % (m.group(1), keyval[key]))
           else:
              try:
                 hardware.add(m.group(1), slot)
              except:
                 print("Ignoring %s: multiple occurrences" % (m.group(1)))
  return hardware
     

if __name__ == '__main__':
  import optparse

  parser = optparse.OptionParser()
  parser.add_option('-f', '--file')
  (options, args) = parser.parse_args()
  if options.file == None:
      raise RuntimeError('-f is mandatory argument')
  vmConfig = LoadVMConfig(options.file)
  if len(args) == 0:
      args = vmConfig.getKnownDevices()
  for dev in args:
      try:
          guestPath = vmConfig.getGuestPCIPath(dev.lower())
      except RuntimeError as e:
          print('%s: %-15s: [%#-8d]' % (e, dev, vmConfig.dev2slot[dev]))
      else:
          print('%s: %-15s: [%#-8d]' % (guestPath, dev, vmConfig.dev2slot[dev]))

