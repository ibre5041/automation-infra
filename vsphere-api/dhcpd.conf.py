import socket

line = "       host {:20}    {{ hardware ethernet {:17}; fixed-address {:15}; }}"
barnBaseIp = "10.0.0.{}"
barnBaseMac = "00:50:56:00:{:02}:{:02}"

for i in range(10, 254):
    try:
        prodIpAddress = "192.168.8." + str(i)
        (highB, lowB) = divmod(i, 100)
        barnIpAddress = barnBaseIp.format(str(i))
        barnMacAddress = barnBaseMac.format(highB, lowB)
        #
        (hostName, _, _) = socket.gethostbyaddr(prodIpAddress)
        hostName = hostName.split('.')[0]
        if "scan" in hostName:
            continue
        #
        print(line.format(hostName, barnMacAddress, barnIpAddress))
    except socket.herror:
        continue
