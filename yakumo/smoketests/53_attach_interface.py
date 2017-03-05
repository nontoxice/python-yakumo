#!/usr/bin/env python
#
# Copyright 2014-2017 by Akira Yoshiyama <akirayoshiyama@gmail.com>.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import time
import re
import yaml

from yakumo.smoketest import *


USER_DATA = r'''#!/bin/sh
i=0
while [ $i -lt 30 ]; do
echo "BeginSysRepo"

CPU=`lscpu | awk '/^CPU.s/ { print $2 }`
echo "vcpus: $CPU"
RAM=`free -m | awk '/^Mem:/ { print $2 }`
echo "ram: $RAM"

echo "disks:"
lsblk -d -n -b | awk '{ print "  " $1 ": { size: " $4 ", type: " $6 " }" }'

echo "nics:"
ip a | sed -re "s/^([0-9])/\n\1/" | awk 'BEGIN { RS="" }
/^[0-9]: eth/ { gsub(":", "", $2);
print "  " $2 ": { mac: \"" $11"\", ip: " $15 " }" }'

echo "EndSysRepo"
done
exit 0
'''


REPORT_PATTERN = re.compile(r'''BeginSysRepo\n(.*?)EndSysRepo''',
                            re.MULTILINE | re.DOTALL)

k = c.key_pair.find_one()
LOG.debug("key pair: %s", k)

f = c.flavor.find_one(name='m1.small')
LOG.debug("flavor: %s", f)

i = c.image.find_one(name='cirros')
LOG.debug("image: %s", i)

n = c.network.find_one(name='private')
LOG.debug("network: %s", n)

n2 = c.network.find_one(name='private2')
LOG.debug("network2: %s", n2)

LOG.debug("list servers: %s", [_.name for _ in c.server.list()])
LOG.debug("list ports: %s", [_.name for _ in c.port.list()])

LOG.info("Create Volume #1")
name = get_random_str('volume')
with c.port.create(name=name, network=n2) as p:

    test("Port #1 is created", p is not None)

    LOG.info("Create Server #1")
    name = get_random_str('server')
    with c.server.create(name=name,
                         networks=[n],
                         image=i,
                         flavor=f,
                         key_pair=k,
                         user_data=USER_DATA) as s:

        LOG.debug("list servers: %s", [_.name for _ in c.server.list()])

        LOG.debug("wait for created")
        s.wait_for_finished()
        test("Server #1 name is " + name, s.name == name)
        test("Server #1 is active", s.status == 'ACTIVE')

        def get_guest_stat(cl):
            match = REPORT_PATTERN.search(cl)
            if match is None:
                return
            return yaml.load(match.group(1))

        for i in range(30):
            time.sleep(10)
            cl = s.get_console_log(lines=20)
            if get_guest_stat(cl):
                break
            if 'login:' in cl:
                raise Exception()
        else:
            raise Exception()

        stat = get_guest_stat(cl)
        LOG.debug("vcpus: %s", stat['vcpus'])
        LOG.debug("ram: %s", stat['ram'])
        LOG.debug("nics: %s", stat['nics'])
        LOG.debug("disks: %s", stat['disks'])

        eth0_mac = stat['nics']['eth0']['mac']
        port0_mac = c.port.find_one(device=s).mac_address
        test("eth0 is a port for Server #1", port0_mac == eth0_mac)

        test("eth1 not found", 'eth1' not in stat['nics'])
        nics = len(stat['nics'])

        LOG.info("Attach a network")
        ia = s.interface.attach(network=n)
        for i in range(30):
            time.sleep(10)
            cl = s.get_console_log(lines=20)
            stat = get_guest_stat(cl)

            if len(stat['nics']) != nics:
                break

        test("eth1 exists", 'eth1' in stat['nics'])

        eth1_mac = stat['nics']['eth1']['mac']
        port1_mac = [_.mac_address for _ in c.port.find(device=s)
                     if _.mac_address != eth0_mac][0]
        test("eth1 is the new port for Server #1", port1_mac == eth1_mac)

        nics = len(stat['nics'])

        LOG.info("Detach a network")
        ia.detach()
        for i in range(30):
            time.sleep(10)
            cl = s.get_console_log(lines=20)
            stat = get_guest_stat(cl)

            if len(stat['nics']) != nics:
                break

        test("eth1 not found", 'eth1' not in stat['nics'])
        nics = len(stat['nics'])

        LOG.info("Attach a port")
        ia = s.interface.attach(port=p)
        for i in range(30):
            time.sleep(10)
            cl = s.get_console_log(lines=20)
            stat = get_guest_stat(cl)

            if len(stat['nics']) != nics:
                break

        test("eth1 exists", 'eth1' in stat['nics'])
        eth1_mac = stat['nics']['eth1']['mac']
        test("eth1 is Port #1", p.mac_address == eth1_mac)

        nics = len(stat['nics'])

        LOG.info("Detach a port")
        ia.detach()
        for i in range(30):
            time.sleep(10)
            cl = s.get_console_log(lines=20)
            stat = get_guest_stat(cl)

            if len(stat['nics']) != nics:
                break

        test("eth1 not found", 'eth1' not in stat['nics'])

    test("Server #1 is deleted", s not in c.server.list())


test("Port #1 is deleted", p not in c.port.list())

LOG.debug("list servers: %s", [_.name for _ in c.server.list()])
LOG.debug("list ports: %s", [_.name for _ in c.port.list()])

show_test_summary()