#
# Copyright (c) 2009, 2010 Testrepository Contributors
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

"""The testrepository tests and test only code."""

import os

import testresources
from testscenarios import generate_scenarios
from testtools import TestCase


class ResourcedTestCase(TestCase, testresources.ResourcedTestCase):
    """Make all testrepository tests have resource support."""


class _Wildcard(object):
    """Object that is equal to everything."""

    def __repr__(self):
        return '*'

    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False


Wildcard = _Wildcard()


class StubTestCommand:

    def __init__(self, filter_tags=None):
        self.results = []
        self.filter_tags = filter_tags or set()

    def __call__(self, ui, repo):
        return self

    def get_filter_tags(self):
        return self.filter_tags


def load_tests(loader, standard_tests, pattern):
    # top level directory cached on loader instance
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern=pattern)
    result = testresources.OptimisingTestSuite()
    result.addTests(generate_scenarios(standard_tests))
    result.addTests(generate_scenarios(package_tests))
    return result
