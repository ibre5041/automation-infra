#!/usr/bin/python

import glob
import os
import argparse
import subprocess
import signal
import time
import json
import sys
import socket
import cx_Oracle

class database():
    
    def __init__(self):
        self.ora_status = 'Down'
        try:
            connection = cx_Oracle.connect(user='/', mode=cx_Oracle.SYSDBA)
            self._cursor = connection.cursor()
        except:
            self._cursor = None
            pass


    def fetch_single_value(self, sql):
        try:
            self._cursor.execute(sql)
            (retval,) = self._cursor.fetchone()
            return retval
        except (cx_Oracle.OperationalError, cx_Oracle.DatabaseError, cx_Oracle.InterfaceError) as e:
            #sys.stderr.write("{} failed with: {}".format(sql, str(e)))
            #raise BaseException("{} failed with: {}".format(sql, str(e)))
            return ""
        except:
            return ""
        
    def instance(self):
        try:
            self._cursor.execute(
                """ SELECT
                floor (sysdate - startup_time),
                trunc (24 * ((sysdate - startup_time) - trunc (sysdate - startup_time))),
                mod (trunc (1440 * ((sysdate - startup_time) - trunc (sysdate - startup_time))), 60),
                mod (trunc (86400 * ((sysdate - startup_time) - trunc (sysdate - startup_time))), 60), status
                FROM v$instance """)
            (self.uptime_d, self.uptime_h, self.uptime_m, self.uptime_s, self.ora_status,) = self._cursor.fetchone()
        except:
            (self.uptime_d, self.uptime_h, self.uptime_m, self.uptime_s, self.ora_status,) = (None, None, None, None, None)
            
        if self.ora_status not in ['STARTED', 'MOUNTED']:
            try:
                self._cursor.execute(""" SELECT database_role, dbid FROM v$database """)
                (self.ora_dg_role, self.ora_dbid,) = self._cursor.fetchone()
            except:
                (self.ora_dg_role, self.ora_dbid,) = (None, None)

            self.sys_tbls = self.fetch_single_value(
                """ SELECT file_name FROM dba_data_files WHERE tablespace_name = 'SYSTEM' AND ROWNUM = 1 """)
        else:
            (self.ora_dg_role, self.ora_dbid, self.sys_tbls) = (None, None, None)
                
        self.banner = self.fetch_single_value(
            """ SELECT banner FROM v$version WHERE banner LIKE '%Oracle Database%' """)
        self.ora_version = self.fetch_single_value(
            """ SELECT version from v$instance """)
        
        # Alert log dest
        diag_dest = self.fetch_single_value(
            """ SELECT max(value) as diag_dest FROM v$parameter WHERE name = 'diagnostic_dest' """)
        if diag_dest:
            self.alert_log = self.fetch_single_value(
                """ SELECT REPLACE(value,'cdump','trace') as alert_log from v$parameter where name ='core_dump_dest' """)
        else:
            self.alert_log = self.fetch_single_value(
                """ SELECT value as alert_log FROM v$parameter WHERE name = 'background_dump_dest' """)

        # This will fail on ASM, DBA_* views are nor accessible
        try:
            if self.ora_version.startswith('12'):
                self.ora_version = self.fetch_single_value(
                    """ select MIN(BUNDLE_ID) KEEP (DENSE_RANK LAST ORDER BY ACTION_TIME) BUNDLE_ID 
                    from dba_registry_sqlpatch where status = 'SUCCESS' """)
            elif self.ora_version.startswith('18'):
                self.ora_version = self.fetch_single_value(
                    """ select max(TARGET_VERSION) KEEP (DENSE_RANK LAST ORDER BY ACTION_TIME) 
                    FROM dba_registry_sqlpatch where status='SUCCESS') """)        
            else: #ora_version.startswith('19'):
                self.ora_version = self.fetch_single_value(
                    """ SELECT distinct REGEXP_SUBSTR(description, '[0-9]{2}.[0-9]{1,2}.[0-9].[0-9].[0-9]{6}') as VER
                    from dba_registry_sqlpatch 
                    where TARGET_VERSION in 
                    (SELECT max(TARGET_VERSION) KEEP (DENSE_RANK LAST ORDER BY ACTION_TIME) as VER 
                    FROM dba_registry_sqlpatch where status='SUCCESS' and FLAGS not like '%J%') and ACTION = 'APPLY' """)
        except BaseException as a:
            pass

        self.ora_dg_on = self.fetch_single_value(
            """ SELECT count(*) as ora_dg_on FROM v$archive_dest WHERE status = 'VALID' AND target = 'STANDBY' """)
        self.ora_rac_on = self.fetch_single_value(
            """ SELECT value as ora_rac_on FROM v$parameter WHERE name = 'cluster_database' """)
        self.ora_rac_nodes = self.fetch_single_value(
            """ SELECT count(*) as ora_rac_nodes FROM v$active_instances """)

    def status(self):
        diag_dest = self.fetch_single_value(
            """ SELECT max(value) as diag_dest FROM v$parameter WHERE name = 'diagnostic_dest' """)
        if diag_dest:
            self.alert_log = self.fetch_single_value(
                """ SELECT REPLACE(value,'cdump','trace') as alert_log from v$parameter where name ='core_dump_dest' """)
        else:
            self.alert_log = self.fetch_single_value(
                """ SELECT value as alert_log FROM v$parameter WHERE name = 'background_dump_dest' """)

        self.ora_sgapga = self.fetch_single_value(
            """ select max(case when name='sga_target' then display_value end) 
            ||'/'|| max(case when name='pga_aggregate_target' then display_value end) as SGAPGA
            from v$parameter where name in ('pga_aggregate_target','sga_target') """)
        
    def __str__(self):
        retval = ''
        for attribute, value in sorted(self.__dict__.items()):
            if attribute.startswith('_'):
                continue
            if value is None:
                value = ''
            retval += "{}='{}'\n".format(attribute, value)
        return retval


class homes():

    def __init__(self):
        self.facts_item = {}
        self.running_only = False
        self.oracle_restart = False
        self.oracle_crs = False
        self.oracle_standalone = False
        self.oracle_install_type = None
        self.crs_home = None
        self.homes = []
        self.ora_inventory = None
        self.orabase = None
        self.crsctl = None
        
        try:
            with open('/etc/oracle/ocr.loc') as f:
                for line in f:
                    if line.startswith('local_only='):
                        (_, local_only,) = line.strip().split('=')
                        if local_only.upper() == 'TRUE':
                            self.oracle_install_type = 'RESTART'
                        if local_only.upper() == 'FALSE':
                            self.oracle_install_type = 'CRS'
        except:
            pass

        try:
            with open('/etc/oracle/olr.loc') as f:
                for line in f:
                    if line.startswith('crs_home='):
                        (_, crs_home,) = line.strip().split('=')
                        self.crs_home = crs_home

                        crsctl = os.path.join(crs_home, 'bin', 'crsctl')
                        if os.access(crsctl, os.X_OK):
                            self.crsctl = crsctl
        except:
            pass

        try:
            with open('/etc/oraInst.loc') as f:
                for line in f:
                    if line.startswith('inventory_loc='):
                        (_, oraInventory,) = line.strip().split('=')
                        self.ora_inventory = oraInventory

            from xml.dom import minidom
            inv_tree = minidom.parse(os.path.join(self.ora_inventory, 'ContentsXML', 'inventory.xml'))
            homes = inv_tree.getElementsByTagName('HOME')
            for home in homes:
                self.homes.append(home.attributes['LOC'].value)
        except:
            pass


    def parse_oratab(self):
        #Reads SID and ORACLE_HOME from oratab
        with open('/etc/oratab','r') as oratab:
            for line in oratab:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    continue

                SID, ORACLE_HOME, _ = line.split(':')
                if self.running_only:
                    if SID in self.facts_item:
                        self.facts_item[SID]['ORACLE_HOME'] = ORACLE_HOME
                    else:
                        #logging.warn('ORACLE_SID: {} is down'.format(SID))
                        pass
                else:
                    if SID in self.facts_item:
                        self.facts_item[SID]['ORACLE_HOME'] = ORACLE_HOME
                    else:
                        self.facts_item[SID] = {'SID': SID, 'ORACLE_HOME': ORACLE_HOME, 'running': False}


    def list_processes(self):
        """
        # Emulate trick form tanelpoder
        # https://tanelpoder.com/2011/02/28/finding-oracle-homes-with/
        #
        # printf "%6s %-20s %-80s\n" "PID" "NAME" "ORACLE_HOME"
        # pgrep -lf _pmon_ |
        #  while read pid pname  y ; do
        #    printf "%6s %-20s %-80s\n" $pid $pname `ls -l /proc/$pid/exe | awk -F'>' '{ print $2 }' | sed 's/bin\/oracle$//' | sort | uniq` 
        #  done
        #
        # It s basically looking up all PMON process IDs and then using /proc/PID/exe link to find out where is the oracle binary of a running process located
        #
        """
        for cmd_line_file in glob.glob('/proc/[0-9]*/cmdline'):
            try:
                with open(cmd_line_file) as x: 
                    cmd_line = x.read().rstrip("\x00")
                    if not cmd_line.startswith('ora_pmon_') and not cmd_line.startswith('asm_pmon_'):
                        continue
                    _, _, SID = cmd_line.split('_')

                    piddir = os.path.dirname(cmd_line_file)
                    exefile = os.path.join(piddir, 'exe')

                    try:
                        if not os.path.islink(exefile):
                            continue
                        oraclefile = os.readlink(exefile)
                        ORACLE_HOME = os.path.dirname(oraclefile)
                        ORACLE_HOME = os.path.dirname(ORACLE_HOME)
                    except:
                        # In case oracle binary is suid, ptrace does not work, 
                        # stat/readlink /proc/<pid>/exec does not work
                        # fails with: Permission denied
                        # Then try to query the same information from CRS
                        ORACLE_HOME = None

                        if self.crsctl:
                            dfilter = '((TYPE = ora.database.type) and (GEN_USR_ORA_INST_NAME = {ORACLE_SID}))'.format(ORACLE_SID=SID)
                            proc = subprocess.Popen([self.crsctl, 'stat', 'res', '-p', '-w', dfilter], stdout=subprocess.PIPE)
                            for line in iter(proc.stdout.readline,''):
                                if line.startswith('ORACLE_HOME='):
                                    (_, ORACLE_HOME,) = line.strip().split('=')
                        pass
                    
                    ORACLE_BASE = self.base_from_home(ORACLE_HOME)
                    self.facts_item[SID]= {'SID': SID, 'ORACLE_HOME': ORACLE_HOME, 'running': True, 'ORACLE_BASE': ORACLE_BASE}

            #except FileNotFoundError: # Python3
            except EnvironmentError as e:
                #print("Missing file ignored: {} ({})".format(cmd_line_file, e))
                pass


    def list_crs_instances(self):
        hostname = socket.gethostname()
        if self.crsctl:
            dfilter = '(TYPE = ora.database.type)'
            proc = subprocess.Popen([self.crsctl, 'stat', 'res', '-p', '-w', dfilter], stdout=subprocess.PIPE)
            (ORACLE_HOME, ORACLE_SID) = (None, None)
            for line in iter(proc.stdout.readline,''):
                if not line.strip():
                    (ORACLE_HOME, ORACLE_SID) = (None, None)
                if 'SERVERNAME({})'.format(hostname) in line and line.startswith('GEN_USR_ORA_INST_NAME'):
                    (_, ORACLE_SID,) = line.strip().split('=')
                if line.startswith('ORACLE_HOME='):
                    (_, ORACLE_HOME,) = line.strip().split('=')
                if ORACLE_SID and ORACLE_HOME:
                    ORACLE_BASE = self.base_from_home(ORACLE_HOME)
                    self.facts_item[ORACLE_SID] = {'SID': ORACLE_SID, 'ORACLE_HOME': ORACLE_HOME, 'running': None, 'ORACLE_BASE': ORACLE_BASE}
                    (ORACLE_HOME, ORACLE_SID) = (None, None)

    def base_from_home(self, ORACLE_HOME):
        """ execute $ORACLE_HOME/bin/orabase to get ORACLE_BASE """
        orabase = os.path.join(ORACLE_HOME, 'bin', 'orabase')
        ORACLE_BASE = None
        if os.access(orabase, os.X_OK):
            proc = subprocess.Popen([orabase], stdout=subprocess.PIPE, env={'ORACLE_HOME': ORACLE_HOME})
            for line in iter(proc.stdout.readline,''):
                if line.strip():
                    ORACLE_BASE = line.strip()
        return ORACLE_BASE


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l', '--homes',    required=False, action='store_true', help='List Oracle HOMEs')
    group.add_argument('-i', '--instance', required=False, action='store_true', help='Describe database instance')
    group.add_argument('-s', '--status', required=False, action='store_true', help='Status of database instance')
    
    parser.add_argument('-d', '--debug', required=False, action='store_true', help='Debug')

    parser.add_argument('-S', '--sid', required=False, action='store', help='ORACLE_SID')
    parser.add_argument('-H', '--home', required=False, action='store', help='ORACLE_HOME')

    args = parser.parse_args()

    if args.homes:
        h = homes()
        h.list_processes()
        h.parse_oratab()
        h.list_crs_instances()

        if args.debug:
            print(json.dumps(h.facts_item, indent=4))
        else:
            for k in sorted(h.facts_item.keys()):
                print("{SID}\t{ORACLE_HOME}\t{ORACLE_BASE}"
                      .format(SID=k
                              , ORACLE_HOME=h.facts_item[k]['ORACLE_HOME']
                              , ORACLE_BASE=h.facts_item[k]['ORACLE_BASE']))

    if args.instance:
        if args.sid:
            os.environ["ORACLE_SID"] = args.sid
        if args.home:
            os.environ["ORACLE_HOME"] = args.home
        d = database()
        d.instance()
        print(str(d))

    if args.status:
        if args.sid:
            os.environ["ORACLE_SID"] = args.sid
        if args.home:
            os.environ["ORACLE_HOME"] = args.home
        d = database()
        d.status()
        print(str(d))
