#!/usr/bin/python
# -*- coding: utf-8 -*-

# 2018, Simon Dodsley (simon@purestorage.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: purefb_alert
version_added: '2.9'
short_description: Configure Pure Storage FlashBlade alert email settings
description:
- Configure alert email configuration for Pure Storage FlashArrays.
- Add or delete an individual syslog server to the existing
  list of serves.
author:
- Simon Dodsley (@sdodsley)
options:
  state:
    type: str
    description:
    - Create or delete alert email
    default: present
    choices: [ absent, present ]
  address:
    type: str
    description:
    - Email address (valid format required)
    required: true
  enabled:
    type: bool
    default: true
    description:
    - Set specified email address to be enabled or disabled
extends_documentation_fragment:
- purestorage.fb
'''

EXAMPLES = r'''
- name: Add new email recipient and enable, or enable existing email
  purefb_alert:
    address: "user@domain.com"
    enabled: true
    state: present
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
- name: Delete existing email recipient
  purefb_alert:
    state: absent
    address: "user@domain.com"
    fb_url: 10.10.10.2
    api_token: e31060a7-21fc-e277-6240-25983c6c4592
'''

RETURN = r'''
'''


HAS_PURITY_FB = True
try:
    from purity_fb import AlertWatcher
except ImportError:
    HAS_PURITY_FB = False


import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.purestorage.flashblade.plugins.module_utils.purefb import get_blade, purefb_argument_spec


def create_alert(module, blade):
    """Create Alert Email"""
    changed = False
    if not module.check_mode:
        try:
            blade.alert_watchers.create_alert_watchers(name=[module.params['address']])
            changed = True
        except Exception:
            module.fail_json(msg='Failed to create alert email: {0}'.format(module.params['address']))

        if not module.params['enabled']:
            try:
                watcher_settings = AlertWatcher(enabled=False)
                blade.alert_watchers.update_alert_watchers(names=[module.params['address']], watcher_settings=watcher_settings)
            except Exception:
                module.fail_json(msg='Failed to enable alert email: {0}'.format(module.params['address']))
    changed = True

    module.exit_json(changed=changed)


def enable_alert(module, blade):
    """Enable Alert Email"""
    changed = False
    if not module.check_mode:
        try:
            watcher_settings = AlertWatcher(enabled=True)
            blade.alert_watchers.update_alert_watchers(names=[module.params['address']], watcher_settings=watcher_settings)
        except Exception:
            module.fail_json(msg='Failed to enable alert email: {0}'.format(module.params['address']))
    changed = True

    module.exit_json(changed=changed)


def disable_alert(module, blade):
    """Disable Alert Email"""
    changed = False
    if not module.check_mode:
        try:
            watcher_settings = AlertWatcher(enabled=False)
            blade.alert_watchers.update_alert_watchers(names=[module.params['address']], watcher_settings=watcher_settings)
        except Exception:
            module.fail_json(msg='Failed to disable alert email: {0}'.format(module.params['address']))
    changed = True

    module.exit_json(changed=changed)


def delete_alert(module, blade):
    """Delete Alert Email"""
    changed = False
    if not module.check_mode:
        try:
            blade.alert_watchers.delete_alert_watchers(name=[module.params['address']])
        except Exception:
            module.fail_json(msg='Failed to delete alert email: {0}'.format(module.params['address']))
    changed = True

    module.exit_json(changed=changed)


def main():
    argument_spec = purefb_argument_spec()
    argument_spec.update(dict(
        address=dict(type='str', required=True),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    ))

    module = AnsibleModule(argument_spec,
                           supports_check_mode=True)

    if not HAS_PURITY_FB:
        module.fail_json(msg='purity_fb SDK is required for this module')


    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    if not pattern.match(module.params['address']):
        module.fail_json(msg='Valid email address not provided.')

    blade = get_blade(module)

    exists = False
    try:
        emails = blade.alert_watchers.list_alert_watchers()
    except Exception:
        module.fail_json(msg='Failed to get exisitng email list')
    for email in range(0, len(emails.items)):
        if emails.items[email].name == module.params['address']:
            exists = True
            enabled = emails.items[email].enabled
            break
    if module.params['state'] == 'present' and not exists:
        create_alert(module, blade)
    elif module.params['state'] == 'present' and exists and not enabled and module.params['enabled']:
        enable_alert(module, blade)
    elif module.params['state'] == 'present' and exists and enabled:
        disable_alert(module, blade)
    elif module.params['state'] == 'absent' and exists:
        delete_alert(module, blade)

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()