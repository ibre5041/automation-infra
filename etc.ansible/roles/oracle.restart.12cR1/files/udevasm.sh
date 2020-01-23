#!/bin/bash

echo "================================================================================" >> /tmp/udevtest2.out
echo >> /tmp/udevtest2.out
echo "Major is: $1" >> /tmp/udevtest2.out
echo "Minor is: $2" >>  /tmp/udevtest2.out
echo "ATTR{manufacturer} is: $3" >>  /tmp/udevtest2.out

env >> /tmp/udevtest2.out

if [[ "${DEVTYPE}" == "partition" && "${DEVNAME}" =~ /dev/[a-z]+([0-9]) ]]; then
PART="p"${BASH_REMATCH[1]}
else
PART=""
fi

[[ $DEVPATH =~ /target([1-9]):[0-9]:([0-9]) ]] && printf "ASMNAME=asmshared%02d%02d%s" ${BASH_REMATCH[1]} ${BASH_REMATCH[2]} "${PART}" >> /tmp/udevtest2.out
[[ $DEVPATH =~ /target([1-9]):[0-9]:([0-9]) ]] && printf "ASMNAME=asmshared%02d%02d%s" ${BASH_REMATCH[1]} ${BASH_REMATCH[2]} "${PART}"


exit 0
