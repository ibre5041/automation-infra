export ORACLE_SID=+ASM{{play_hosts.index(inventory_hostname) + 1 }}
export CRS_HOME=/oracle/u01/gi/{{ oracle_ver_path }}
export ORACLE_BASE=/oracle/u01/base
export ORACLE_HOME=/oracle/u01/gi/{{ oracle_ver_path }}

export NLS_DATE_FORMAT='dd/mm/yyyy hh24:mi'
export PATH=$(echo $PATH | sed 's/oracle.*\/bin//g'):$ORACLE_HOME/bin
export NLS_LANG=_.AL32UTF8
