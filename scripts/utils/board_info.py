#!/usr/bin/python3

# Description: This script is used to get network interfaces,
# IP address, netmask and broadcast from device under test.

import subprocess
import json
import re
import os
import sys
from shutil import copyfile
from create_archives import *

def get_ipaddr(iface):
    cmd = "_RAW_STREAM_V4=`/sbin/ifconfig %s | \
           grep -o -E '([[:xdigit:]]{1,3}\.){3}[[:xdigit:]]{1,3}'`; \
           echo $_RAW_STREAM_V4 | awk '{print$1}'" % iface
    return subprocess.check_output(cmd, shell=True).decode().strip('\n')

def get_broadcast(iface):
    cmd = "_RAW_STREAM_V4=`/sbin/ifconfig %s | \
           grep -o -E '([[:xdigit:]]{1,3}\.){3}[[:xdigit:]]{1,3}'`; \
           echo $_RAW_STREAM_V4 | awk '{print$3}'" % iface
    return subprocess.check_output(cmd, shell=True).decode().strip('\n')

def get_macaddr(iface):
    cmd = "/sbin/ifconfig %s |grep HWaddr" % iface
    output = subprocess.check_output(cmd, shell=True).decode().strip('\n').split()
    macaddr = output[len(output)-1]
    return macaddr

def show_netinfo():
    cmd = "IFACES=`/sbin/ifconfig | \
           grep -E 'eno[0-9]|ens[0-9]|eth[0-9]|enp[0-9]'`; \
           echo $IFACES | awk  '{ print $1 }'"
    iface = subprocess.check_output(cmd, shell=True).decode().strip('\n')
    print('INFO: Detected network interface... %s' % iface)
    net_info = {}
    net_info = {"interface": iface, 
                "ipaddr": get_ipaddr(iface), 
                "broadcast": get_broadcast(iface), 
                "macaddr": get_macaddr(iface)}
    return net_info

def get_kernel_version():
    return subprocess.check_output(['uname', '-r']).decode().strip('\n')

def get_hostname():
    return subprocess.check_output(['hostname']).decode().strip('\n')

def create_info_file(data, path, filename='board_info.json'):
    file_json = os.path.join(path, filename)
    #print(json.dumps(data, sort_keys=False, indent=4, separators=(',',': ')))
    with open(file_json, 'w') as f:
        f.write(json.dumps(data, sort_keys=False, indent=4, separators=(',',': ')))
        f.close()

def load_board_info(filename):
    print('read file %s' % filename)
    with open(filename) as f:
        data = json.load(f)
        print('read from json file')
        print('kernel: %s' % data['kernel'])
        print('ipaddr: %s' % data['network']['ipaddr'])

def get_lava_job_id():
    list_dir = [f for f in os.listdir('/') if re.match(r'lava',f)]
    return list_dir[0].replace("lava-", "")

def copy_to(src, dest, filename):
    if not os.path.exists(dest):
        print('INFO: Directory in %s is not exist. Creating it...' % dest)
        os.makedirs(dest)
        os.chmod(dest, 0o777)
    dest = os.path.join(dest, filename)
    print('INFO: copy from %s to %s' %(src, dest))
    copyfile(src, dest)

def get_user():
    return subprocess.check_output(['whoami']).decode().strip('\n')

def get_board_info(dest):
    f_board_info = os.path.join(dest, get_lava_job_id())
    f_board_info = os.path.join(f_board_info, 'board_info.json')
    return f_board_info

def update_board_info(path_board_info, data):
    b_info = os.path.join(path_board_info, 'board_info.json')
    with open(b_info) as f:
        feed = json.load(f)
    feed.update(data)
    with open(b_info, 'w') as f:
        json.dump(feed, f, sort_keys=False, indent=4, separators=(',',': '))

def create_lava_dir():
    ww_dir = create_archives_by_daily(None, True)
    lava_dir = os.path.join(ww_dir, 'lava')
    lava_id = get_lava_dir()
    for i in lava_id:
        lava_dir = os.path.join(lava_dir, i)
    if not os.path.exists(lava_dir):
        os.makedirs(lava_dir)
    return lava_dir

if __name__ == "__main__":
    data = {"lava_job_id": get_lava_job_id(), 
            "kernel": get_kernel_version(), 
            "user": get_user(), 
            "hostname": get_hostname(), 
            "network": show_netinfo()}
    path = '/home/root'
    json_file = 'board_info.json'
    create_info_file(data, path, json_file)
    info_file = os.path.join(path, json_file)
    print('INFO: Board info was created at %s' % (os.path.join(path, json_file)))
    dest_board_info = get_board_info('/srv/data/LAVA/lava-job')
    copy_to(info_file, dest_board_info , json_file)
    copy_to(info_file, create_lava_dir(), json_file)

