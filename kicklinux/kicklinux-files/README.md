This is set of the scripts used in post-duplicate script.

It should use information stored in .vmx file (guestinfo) and use it to configure networking using nmcli.

scp nmcli.sh nmcli.flag  rhel7-a:~/

scp vmware-clone-boot.service rhel7-a:/etc/systemd/system/vmware-clone-boot.service
ssh rhel7-a "systemctl enable vmware-clone-boot.service"
