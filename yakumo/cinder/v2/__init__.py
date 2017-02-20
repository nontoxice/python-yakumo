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

"""
Sub client class for Cinder API V2
"""

from . import consistency_group
from . import consistency_group_snapshot
from . import qos
from . import quota_set
from . import service
from . import snapshot
from . import volume
from . import volume_backup
from . import volume_transfer
from . import volume_type


class Client(object):

    def __init__(self, client, *args, **kwargs):
        self.consistency_group = consistency_group.Manager(client)
        self.consistency_group_snapshot = \
            consistency_group_snapshot.Manager(client)
        self.quota_set = quota_set.Manager(client)
        self.service = service.Manager(client)
        self.volume = volume.Manager(client)
        self.volume_backup = volume_backup.Manager(client)
        self.volume_snapshot = snapshot.Manager(client)
        self.volume_transfer = volume_transfer.Manager(client)
        self.volume_type = volume_type.Manager(client)
        self.volume_type_qos = qos.Manager(client)

        client.consistency_group = self.consistency_group
        client.consistency_group_snapshot = self.consistency_group_snapshot
        client.volume = self.volume
        client.volume_backup = self.volume_backup
        client.volume_snapshot = self.volume_snapshot
        client.volume_transfer = self.volume_transfer
        client.volume_type = self.volume_type
        client.volume_type_qos = self.volume_type_qos
