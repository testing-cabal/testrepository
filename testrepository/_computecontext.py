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

from collections import namedtuple

Instance = namedtuple('Instance', 'id')


class Cache:
    """A cache of instances."""

    def __init__(self):
        self._allocated = set()
        self._available = set()

    def add(self, instance):
        """Add an instance to the cache."""
        self._available.add(instance)

    def allocate(self):
        """Allocate an instance from available to allocated.
        
        :return: An Instance.
        """
        instance = self._available.pop()
        self._allocated.add(instance)
        return instance

    def all(self):
        """Return an iterable of all instances."""
        return frozenset(self._allocated.union(self._available))

    def release(self, instance):
        """Return instance to the available pool.
        
        :param instance: An allocated instance.
        """
        self._allocated.remove(instance)
        self._available.add(instance)

    def remove(self, instance):
        """Remove instance from the cache.
        
        :param instance: An allocated instance.
        """
        self._allocated.remove(instance)

    def size(self):
        """Return the number of instances in the cache.

        This is the sum of the number of available and allocated instances.
        """
        return len(self._allocated) + len(self._available)
