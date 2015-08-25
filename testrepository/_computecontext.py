#
# Copyright (c) 2015 Testrepository Contributors
#
# Licensed under either the Apache License, Version 2.0 or the BSD 3-clause
# license at the users choice. A copy of both licenses are available in the
# project source as Apache-2.0 and BSD. You may not use this file except in
# compliance with one of these two licences.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under these licenses is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# license you chose for the specific language governing permissions and
# limitations under that license.

"""Abstracts the idea of a place to run computations."""

__all__ = ['Cache', 'Instance']

from collections import defaultdict, namedtuple
from itertools import chain

import six

_Instance = namedtuple('Instance', ['profile', 'id'])
class Instance(_Instance):

    def __init__(self, *args):
        for arg in args:
            if arg is not None and type(arg) is not six.text_type:
                raise ValueError('Bad argument %r' % (arg,))


class Cache:
    """A cache of instances."""

    def __init__(self):
        self._allocated = defaultdict(set)
        self._available = defaultdict(set)

    def add(self, instance):
        """Add an instance to the cache."""
        self._available[instance.profile].add(instance)

    def allocate(self, profile):
        """Allocate an instance from available to allocated.
        
        :param profile: The profile to allocate for.
        :return: An Instance.
        """
        instance = self._available[profile].pop()
        self._allocated[profile].add(instance)
        return instance

    def all(self):
        """Return an iterable of all instances."""
        instances = set()
        return frozenset(reduce(
            lambda l, r: l.union(r),
            chain(self._available.values(), self._allocated.values()),
            set()))

    def release(self, instance):
        """Return instance to the available pool.
        
        :param instance: An allocated instance.
        """
        self._allocated[instance.profile].remove(instance)
        self._available[instance.profile].add(instance)

    def remove(self, instance):
        """Remove instance from the cache.
        
        :param instance: An allocated instance.
        """
        self._allocated[instance.profile].remove(instance)

    def size(self, instance):
        """Return the number of instances in the cache.

        This is the sum of the number of available and allocated instances.
        """
        return len(self._available[instance]) + len(self._allocated[instance])
