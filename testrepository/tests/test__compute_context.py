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

"""Tests for the _computecontext module."""

from __future__ import unicode_literals

from testrepository._computecontext import (
    Cache,
    Instance,
    )
from testrepository.tests import ResourcedTestCase

class TestInstance(ResourcedTestCase):

    def test_fields(self):
        instance = Instance('profile', '1')
        self.assertEqual('profile', instance.profile)
        self.assertEqual('1', instance.id)

    def test_can_be_put_in_set(self):
        instances = set()
        instances.add(Instance('profile', '2'))

    def test_rejects_bytes(self):
        self.assertRaises(ValueError, Instance, 'profile', b'1')
        self.assertRaises(ValueError, Instance, b'profile', '1')


class TestCache(ResourcedTestCase):

    def test_create(self):
        cache = Cache()
        self.assertNotEqual(cache, None)

    def test_smoke(self):
        cache = Cache()
        instance = Instance('profile', '1')
        cache.add(instance)
        # Can't remove unallocated instances.
        self.assertRaises(KeyError, cache.remove, instance)
        self.assertIs(instance, cache.allocate('profile'))
        cache.release(instance)
        self.assertEqual(1, cache.size('profile'))
        self.assertIs(instance, cache.allocate('profile'))
        self.assertEqual(1, cache.size('profile'))
        cache.remove(instance)
        self.assertEqual(0, cache.size('profile'))
        self.assertRaises(KeyError, cache.remove, instance)

    def test_all(self):
        cache = Cache()
        instance1 = Instance('p1', '1')
        instance2 = Instance('p2', '2')
        instance3 = Instance('p1', '3')
        instance4 = Instance('p2', '4')
        cache.add(instance1)
        cache.add(instance2)
        cache.add(instance3)
        cache.add(instance4)
        cache.allocate('p1')
        cache.allocate('p2')
        self.assertEqual(
            frozenset([instance1, instance2, instance3, instance4]),
            cache.all())

    def test_size(self):
        cache = Cache()
        instance1 = Instance('p1', '1')
        instance2 = Instance('p2', '2')
        instance3 = Instance('p1', '3')
        instance4 = Instance('p2', '4')
        cache.add(instance1)
        cache.add(instance2)
        cache.add(instance3)
        cache.add(instance4)
        cache.allocate('p1')
        cache.allocate('p2')
        self.assertEqual(2, cache.size('p1'))
        self.assertEqual(2, cache.size('p2'))

    def test_allocate_empty(self):
        self.assertRaises(Exception, Cache().allocate, 'p1')

    def test_allocate_profile_empty(self):
        c = Cache()
        c.add(Instance('p1', '1'))
        self.assertRaises(Exception, c.allocate, 'p2')
