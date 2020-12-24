#!/usr/bin/env python
# Copyright 2020 The StackStorm Authors.
# Copyright 2019 Extreme Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import collections
import importlib
import six
import sys
import traceback

from oslo_config import cfg


CONFIGS = ['st2actions.config',
           'st2actions.scheduler.config',
           'st2actions.notifier.config',
           'st2actions.workflows.config',
           'st2api.config',
           'st2stream.config',
           'st2auth.config',
           'st2common.config',
           'st2exporter.config',
           'st2reactor.rules.config',
           'st2reactor.sensor.config',
           'st2reactor.timer.config',
           'st2reactor.garbage_collector.config']

SKIP_GROUPS = ['api_pecan', 'rbac', 'results_tracker']

# We group auth options together to make it a bit more clear what applies where
AUTH_OPTIONS = {
    'common': [
        'enable',
        'mode',
        'logging',
        'api_url',
        'token_ttl',
        'service_token_ttl',
        'sso',
        'sso_backend',
        'sso_backend_kwargs',
        'debug'
    ],
    'standalone': [
        'host',
        'port',
        'use_ssl',
        'cert',
        'key',
        'backend',
        'backend_kwargs'
    ]
}

# Some of the config values change depending on the environment where this script is ran so we
# set them to static values to ensure consistent and stable output
STATIC_OPTION_VALUES = {
    'actionrunner': {
        'virtualenv_binary': '/usr/bin/virtualenv',
        'python_binary': '/usr/bin/python',
        'python3_binary': '/usr/bin/python3'
    },
    'webui': {
        'webui_base_url': 'https://localhost'
    }
}

COMMON_AUTH_OPTIONS_COMMENT = """
# Common option - options below apply in both scenarios - when auth service is running as a WSGI
# service (e.g. under Apache or Nginx) and when it's running in the standalone mode.
""".strip()

STANDALONE_AUTH_OPTIONS_COMMENT = """
# Standalone mode options - options below only apply when auth service is running in the standalone
# mode.
""".strip()


def _import_config(config):
    try:
        return importlib.import_module(config)
    except:
        traceback.print_exc()
    return None


def _read_current_config(opt_groups):
    for k, v in six.iteritems(cfg.CONF._groups):
        if k in SKIP_GROUPS:
            continue
        if k not in opt_groups:
            opt_groups[k] = v
    return opt_groups


def _clear_config():
    cfg.CONF.reset()


def _read_group(opt_group):
    all_options = list(opt_group._opts.values())

    if opt_group.name == 'auth':
        print(COMMON_AUTH_OPTIONS_COMMENT)
        print('')
        common_options = [option for option in all_options if option['opt'].name in
                          AUTH_OPTIONS['common']]
        _print_options(opt_group=opt_group, options=common_options)

        print('')
        print(STANDALONE_AUTH_OPTIONS_COMMENT)
        print('')
        standalone_options = [option for option in all_options if option['opt'].name in
                              AUTH_OPTIONS['standalone']]
        _print_options(opt_group=opt_group, options=standalone_options)

        if len(common_options) + len(standalone_options) != len(all_options):
            msg = ('Not all options are declared in AUTH_OPTIONS dict, please update it')
            raise Exception(msg)
    else:
        options = all_options
        _print_options(opt_group=opt_group, options=options)


def _read_groups(opt_groups):
    opt_groups = collections.OrderedDict(sorted(opt_groups.items()))
    for name, opt_group in six.iteritems(opt_groups):
        print('[%s]' % name)
        _read_group(opt_group)
        print('')


def _print_options(opt_group, options):
    for opt in sorted(options, key=lambda x: x['opt'].name):
        opt = opt['opt']

        # Special case for options which could change during this script run
        static_option_value = STATIC_OPTION_VALUES.get(opt_group.name, {}).get(opt.name, None)
        if static_option_value:
            opt.default = static_option_value

        # Special handling for list options
        if isinstance(opt, cfg.ListOpt):
            if opt.default:
                value = ','.join(opt.default)
            else:
                value = ''

            value += ' # comma separated list allowed here.'
        else:
            value = opt.default

        print('# %s' % opt.help)
        print('%s = %s' % (opt.name, value))


def main(args):
    opt_groups = {}
    for config in CONFIGS:
        mod = _import_config(config)
        mod.register_opts()
        _read_current_config(opt_groups)
        _clear_config()
    _read_groups(opt_groups)


if __name__ == '__main__':
    main(sys.argv)
