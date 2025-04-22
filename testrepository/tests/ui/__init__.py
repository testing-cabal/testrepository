#
# Copyright (c) 2009 Testrepository Contributors
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

"""Tests for ui modules."""

import unittest


def test_suite():
    names = [
        "cli",
        "decorator",
    ]
    module_names = ["testrepository.tests.ui.test_" + name for name in names]
    loader = unittest.TestLoader()
    return loader.loadTestsFromNames(module_names)
