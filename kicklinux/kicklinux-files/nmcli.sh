#!/bin/sh

IP_P=`vmtoolsd --cmd 'info-get guestinfo.prod_ip'`
IP_B=`vmtoolsd --cmd 'info-get guestinfo.barn_ip'`
DNS=`vmtoolsd --cmd 'info-get guestinfo.dns'`
H=`vmtoolsd --cmd 'info-get guestinfo.hostname'`

exec > /root/nmcli.log

touch /root/nmcli.flag

if [ -n "${H}" ]; then
    nmcli general hostname "${H}"
fi

if [ -n "${IP_P}" ]; then
    nmcli con del ens224
    nmcli con del ens192

    nmcli con add save yes con-name net-prod ifname ens224 type ethernet ip4 ${IP_P}/24 gw4 192.168.8.1
    nmcli con add save yes con-name net-barn ifname ens192 type ethernet ip4 ${IP_B}/24

    nmcli con mod net-prod connection.autoconnect yes
    nmcli con mod net-barn connection.autoconnect yes

    nmcli networking off
    nmcli general status
    nmcli networking on

    rm -f /root/nmcli.flag

    # in case when sdb [vg01] was extended during clonning, try to extend PV too, but only once
    parted -s /dev/sdb resizepart 1 100%
    pvresize /dev/sdb1
fi

if [ -n "${DNS}" ]; then
    nmcli con mod net-prod +ipv4.dns ${DNS}
    nmcli con mod net-prod +ipv4.dns-search prod.vmware.haf
fi


