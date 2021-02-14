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

try:
    import simplejson as json
    from simplejson import JSONEncoder
except ImportError:
    import json
    from json import JSONEncoder

import orjson

import six


__all__ = [
    'json_encode',
    'json_decode',

    'json_loads',
    'try_loads',

    'get_json_type_for_python_value'
]


class GenericJSON(JSONEncoder):
    def default(self, obj):  # pylint: disable=method-hidden
        if hasattr(obj, '__json__') and six.callable(obj.__json__):
            return obj.__json__()
        else:
            return JSONEncoder.default(self, obj)


def default(obj):
    if hasattr(obj, '__json__') and six.callable(obj.__json__):
        return obj.__json__()
    elif isinstance(obj, bytes):
        # TODO: We should update the code which passes bytes to pass unicode to avoid this
        # conversion here
        return  obj.decode("utf-8")
    raise TypeError


def json_encode(obj, indent=None):
#def json_encode(obj, indent=4):
    if indent:
        return orjson.dumps(obj, default=default, option=orjson.OPT_INDENT_2)

    # NOTE: We don't use indent by default since it's quite a bit slower
    return orjson.dumps(obj, default=default)
    #return json.dumps(obj, cls=GenericJSON, indent=indent)


def json_decode(data):
    return orjson.loads(data)


def load_file(path):
    with open(path, 'r') as fd:
        return json.load(fd)


def json_loads(obj, keys=None):
    """
    Given an object, this method tries to json.loads() the value of each of the keys. If json.loads
    fails, the original value stays in the object.

    :param obj: Original object whose values should be converted to json.
    :type obj: ``dict``

    :param keys: Optional List of keys whose values should be transformed.
    :type keys: ``list``

    :rtype ``dict`` or ``None``
    """
    if not obj:
        return None

    if not keys:
        keys = list(obj.keys())

    for key in keys:
        try:
            obj[key] = json_decode(obj[key])
        except:
            pass
    return obj


def try_loads(s):
    try:
        return json_decode(s) if s and isinstance(s, six.string_types) else s
    except:
        return s


def get_json_type_for_python_value(value):
    """
    Return JSON type string for the provided Python value.

    :rtype: ``str``
    """
    if isinstance(value, six.text_type):
        return 'string'
    elif isinstance(value, (int, float)):
        return 'number'
    elif isinstance(value, dict):
        return 'object'
    elif isinstance(value, (list, tuple)):
        return 'array'
    elif isinstance(value, bool):
        return 'boolean'
    elif value is None:
        return 'null'
    else:
        return 'unknown'
