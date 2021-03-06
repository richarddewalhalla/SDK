# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Defines tool-wide constants."""
import os

from googlecloudsdk.third_party.py27 import py27_collections as collections

BYTES_IN_ONE_GB = 2 ** 30

DEFAULT_STANDARD_DISK_SIZE_GB = 500
DEFAULT_SSD_DISK_SIZE_GB = 100
STANDARD_DISK_PERFORMANCE_WARNING_GB = 200
SSD_DISK_PERFORMANCE_WARNING_GB = 10

# The maximum number of results that can be returned in a single list
# response.
MAX_RESULTS_PER_PAGE = 500

# Defaults for instance creation.
DEFAULT_ACCESS_CONFIG_NAME = 'external-nat'

DEFAULT_MACHINE_TYPE = 'n1-standard-1'
DEFAULT_NETWORK = 'default'

DEFAULT_IMAGE = 'debian-8'

ImageAlias = collections.namedtuple(
    'ImageAlias', ['project', 'name_prefix'])

IMAGE_ALIASES = {
    'centos-6': ImageAlias(project='centos-cloud', name_prefix='centos-6'),
    'centos-7': ImageAlias(project='centos-cloud', name_prefix='centos-7'),
    'container-vm': ImageAlias(
        project='google-containers', name_prefix='container-vm'),
    'coreos': ImageAlias(project='coreos-cloud', name_prefix='coreos-stable'),
    'debian-7':
        ImageAlias(project='debian-cloud', name_prefix='debian-7-wheezy'),
    'debian-7-backports': ImageAlias(
        project='debian-cloud', name_prefix='backports-debian-7-wheezy'),
    'debian-8':
        ImageAlias(project='debian-cloud', name_prefix='debian-8-jessie'),
    'opensuse-13': ImageAlias(
        project='opensuse-cloud', name_prefix='opensuse-13'),
    'rhel-6': ImageAlias(project='rhel-cloud', name_prefix='rhel-6'),
    'rhel-7': ImageAlias(project='rhel-cloud', name_prefix='rhel-7'),
    'sles-11': ImageAlias(project='suse-cloud', name_prefix='sles-11'),
    'sles-12': ImageAlias(project='suse-cloud', name_prefix='sles-12'),
    'ubuntu-12-04': ImageAlias(
        project='ubuntu-os-cloud', name_prefix='ubuntu-1204-precise'),
    'ubuntu-14-04': ImageAlias(
        project='ubuntu-os-cloud', name_prefix='ubuntu-1404-trusty'),
    'ubuntu-15-04': ImageAlias(
        project='ubuntu-os-cloud', name_prefix='ubuntu-1504-vivid'),
    'ubuntu-15-10': ImageAlias(
        project='ubuntu-os-cloud', name_prefix='ubuntu-1510-wily'),
    'windows-2008-r2': ImageAlias(
        project='windows-cloud', name_prefix='windows-server-2008-r2'),
    'windows-2012-r2': ImageAlias(
        project='windows-cloud', name_prefix='windows-server-2012-r2'),
}

# These are like IMAGE_ALIASES, but don't show up in the alias list.
HIDDEN_IMAGE_ALIASES = {
    'gae-builder-vm':
        ImageAlias(project='goog-vmruntime-images',
                   name_prefix='gae-builder-vm'),
}

WINDOWS_IMAGE_PROJECT = 'windows-cloud'
PUBLIC_IMAGE_PROJECTS = [
    'centos-cloud',
    'coreos-cloud',
    'debian-cloud',
    'opensuse-cloud',
    'rhel-cloud',
    'suse-cloud',
    'ubuntu-os-cloud',
    WINDOWS_IMAGE_PROJECT,
]
PREVIEW_IMAGE_PROJECTS = []

# SSH-related constants.
DEFAULT_SSH_KEY_FILE = os.path.join('~', '.ssh', 'google_compute_engine')
SSH_KEYS_METADATA_KEY = 'sshKeys'
SSH_KEYS_INSTANCE_RESTRICTED_METADATA_KEY = 'ssh-keys'
SSH_KEYS_BLOCK_METADATA_KEY = 'block-project-ssh-keys'
MAX_METADATA_VALUE_SIZE_IN_BYTES = 32768
PER_USER_SSH_CONFIG_FILE = os.path.join('~', '.ssh', 'config')

_STORAGE_RO = 'https://www.googleapis.com/auth/devstorage.read_only'
_USERACCOUNTS_RO = 'https://www.googleapis.com/auth/cloud.useraccounts.readonly'
_LOGGING_WRITE = 'https://www.googleapis.com/auth/logging.write'
_MONITORING_WRITE = 'https://www.googleapis.com/auth/monitoring.write'
_SERVICE_CONTROL_SCOPE = 'https://www.googleapis.com/auth/servicecontrol'
_SERVICE_MANAGEMENT_SCOPE = 'https://www.googleapis.com/auth/service.management'

DEFAULT_SCOPES = sorted([
    _STORAGE_RO, _USERACCOUNTS_RO, _LOGGING_WRITE, _MONITORING_WRITE,
    _SERVICE_CONTROL_SCOPE, _SERVICE_MANAGEMENT_SCOPE,
])

SCOPES = {
    'bigquery': 'https://www.googleapis.com/auth/bigquery',
    'cloud-platform': 'https://www.googleapis.com/auth/cloud-platform',
    'compute-ro': 'https://www.googleapis.com/auth/compute.readonly',
    'compute-rw': 'https://www.googleapis.com/auth/compute',
    'useraccounts-ro': _USERACCOUNTS_RO,
    'useraccounts-rw': 'https://www.googleapis.com/auth/cloud.useraccounts',
    'datastore': 'https://www.googleapis.com/auth/datastore',
    'logging-write': _LOGGING_WRITE,
    'monitoring': 'https://www.googleapis.com/auth/monitoring',
    'monitoring-write': _MONITORING_WRITE,
    'service-control': _SERVICE_CONTROL_SCOPE,
    'service-management': _SERVICE_MANAGEMENT_SCOPE,
    'sql': 'https://www.googleapis.com/auth/sqlservice',
    'sql-admin': 'https://www.googleapis.com/auth/sqlservice.admin',
    'storage-full': 'https://www.googleapis.com/auth/devstorage.full_control',
    'storage-ro': _STORAGE_RO,
    'storage-rw': 'https://www.googleapis.com/auth/devstorage.read_write',
    'taskqueue': 'https://www.googleapis.com/auth/taskqueue',
    'userinfo-email': 'https://www.googleapis.com/auth/userinfo.email',
}

