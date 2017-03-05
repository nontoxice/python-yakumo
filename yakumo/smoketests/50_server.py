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

from yakumo.smoketest import *


k = c.key_pair.find_one()
LOG.debug("key pair: %s", k)

f = c.flavor.find_one(name='m1.small')
LOG.debug("flavor: %s", f)

i = c.image.find_one(name='cirros')
LOG.debug("image: %s", i)

n = c.network.find_one(name='private')
LOG.debug("network: %s", n)

az = c.availability_zone.get_empty('nova')
LOG.debug("availability zone: %s", az)

LOG.debug("list servers: %s", [_.name for _ in c.server.list()])

LOG.info("Create Server #1")
name = get_random_str('server')
with c.server.create(name=name,
                     networks=[n],
                     image=i,
                     flavor=f,
                     availability_zone=az,
                     key_pair=k) as s:

    LOG.debug("list servers: %s", [_.name for _ in c.server.list()])

    LOG.debug("wait for created")
    s.wait_for_finished()
    test("Server #1 name is " + name, s.name == name)
    test("Server #1 is active", s.status == 'ACTIVE')
    test("Server #1 az is " + az.name, s.availability_zone == az)

    LOG.info("wait for guest OS booted")
    for i in range(30):
        time.sleep(10)
        cl = s.get_console_log(lines=20)
        if 'login:' in cl:
            test("Guest OS is ready", True)
            break
    else:
        test("Guest OS is ready", False)

    LOG.info("Stop Server #1")
    s.stop()
    LOG.debug("wait for stopped")
    s.wait_for_finished()
    test("Server #1 is stopped", s.status == 'SHUTOFF')

    LOG.info("Start Server #1")
    s.start()
    LOG.debug("wait for started")
    s.wait_for_finished()
    test("Server #1 is active", s.status == 'ACTIVE')

    LOG.info("Force reboot Server #1")
    s.reboot(force=True)
    LOG.debug("wait for started")
    s.wait_for_finished()
    test("Server #1 is active", s.status == 'ACTIVE')

    LOG.info("Suspend Server #1")
    s.suspend()
    LOG.debug("wait for suspended")
    s.wait_for_finished()
    test("Server #1 is suspended", s.status == 'SUSPENDED')

    LOG.info("Resume Server #1")
    s.resume()
    LOG.debug("wait for resumed")
    s.wait_for_finished()
    test("Server #1 is active", s.status == 'ACTIVE')

    LOG.info("Pause Server #1")
    s.pause()
    LOG.debug("wait for paused")
    s.wait_for_finished()
    test("Server #1 is paused", s.status == 'PAUSED')

    LOG.info("Unpause Server #1")
    s.unpause()
    LOG.debug("wait for unpaused")
    s.wait_for_finished()
    test("Server is active", s.status == 'ACTIVE')

    LOG.info("Lock Server #1")
    s.lock()
    LOG.debug("wait for locked")
    s.wait_for_finished()
    test("Server #1 is active", s.status == 'ACTIVE')

    LOG.info("Stop Server #1 locked (will be failed)")
    try:
        s.stop()
        s.wait_for_finished()
    except:
        pass
    test("Server #1 is active", s.status == 'ACTIVE')

    LOG.info("Unlock Server #1")
    s.unlock()
    LOG.debug("wait for unlocked")
    s.wait_for_finished()

    LOG.info("Stop Server #1 unlocked (will be succeeded)")
    try:
        s.stop()
        s.wait_for_finished()
    except:
        pass
    test("Server #1 is stopped", s.status == 'SHUTOFF')

    LOG.info("Show Server #1 action: %s",
             [_['action'] for _ in s.get_actions()])

test("Server #1 is deleted", s not in c.server.list())

LOG.debug("list servers: %s", [_.name for _ in c.server.list()])
show_test_summary()