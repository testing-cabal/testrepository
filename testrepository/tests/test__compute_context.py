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

from testrepository._computecontext import (
    Cache,
    Instance,
    )
from testrepository.tests import ResourcedTestCase

class TestInstance(ResourcedTestCase):

    def test_fields(self):
        instance = Instance('1')
        self.assertEqual('1', instance.id)

    def test_in_set(self):
        instances = set()
        instances.add(Instance('2'))


class TestCache(ResourcedTestCase):

    def test_create(self):
        cache = Cache()
        self.assertNotEqual(cache, None)

    def test_smoke(self):
        cache = Cache()
        instance = Instance('1')
        cache.add(instance)
        # Can't remove unallocated instances.
        self.assertRaises(KeyError, cache.remove, instance)
        self.assertIs(instance, cache.allocate())
        cache.release(instance)
        self.assertEqual(1, cache.size())
        self.assertIs(instance, cache.allocate())
        self.assertEqual(1, cache.size())
        cache.remove(instance)
        self.assertEqual(0, cache.size())
        self.assertRaises(KeyError, cache.remove, instance)

    def test_all(self):
        cache = Cache()
        instance1 = Instance('1')
        instance2 = Instance('2')
        cache.add(instance1)
        cache.add(instance2)
        cache.allocate()
        self.assertEqual(2, cache.size())

    def test_allocat_empty(self):
        self.assertRaises(KeyError, Cache().allocate)
