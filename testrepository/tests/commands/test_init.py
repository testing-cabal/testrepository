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

"""Tests for the init command."""

from testrepository.commands import init
from testrepository.ui.model import UI
from testrepository.tests import ResourcedTestCase
from testrepository.tests.test_repository import RecordingRepositoryFactory
from testrepository.repository import memory


class TestCommandInit(ResourcedTestCase):
    def test_init_no_args_no_questions_no_output(self):
        ui = UI()
        cmd = init.init(ui)
        calls = []
        cmd.repository_factory = RecordingRepositoryFactory(
            calls, memory.RepositoryFactory()
        )
        cmd.execute()
        self.assertEqual([("initialise", ui.here)], calls)
