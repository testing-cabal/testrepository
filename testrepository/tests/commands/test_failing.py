#
# Copyright (c) 2010 Testrepository Contributors
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

"""Tests for the failing command."""

import doctest
from io import BytesIO
import os.path
import json
import textwrap

from subunit.v2 import ByteStreamToStreamResult
import testtools
from testtools.compat import _b
from testtools.matchers import (
    DocTestMatches,
    Equals,
    )
from testtools.testresult.doubles import StreamResult

from testrepository.commands import failing
from testrepository.ui.model import UI
from testrepository.repository import memory
from testrepository.tests import (
    ResourcedTestCase,
    StubTestCommand,
    Wildcard,
    )
from testrepository.tests.stubpackage import TempDirResource


class TestFailingBase(ResourcedTestCase):

    def get_test_ui_and_cmd(self, options=(), args=()):
        ui = UI(options=options, args=args)
        cmd = failing.failing(ui)
        ui.set_command(cmd)
        return ui, cmd


class TestCommand(TestFailingBase):

    def test_shows_failures_from_last_run(self):
        ui, cmd = self.get_test_ui_and_cmd()
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        inserter.status(test_id='failing', test_status='fail')
        inserter.status(test_id='ok', test_status='success')
        inserter.stopTestRun()
        self.assertEqual(1, cmd.execute())
        # We should have seen test outputs (of the failure) and summary data.
        self.assertEqual([
            ('results', Wildcard),
            ('summary', False, 1, None, Wildcard, None, [('id', 0, None), ('failures', 1, None)])],
            ui.outputs)
        suite = ui.outputs[0][1]
        result = testtools.StreamSummary()
        result.startTestRun()
        try:
            suite.run(result)
        finally:
            result.stopTestRun()
        self.assertEqual(1, result.testsRun)
        self.assertEqual(1, len(result.errors))

    def test_with_subunit_shows_subunit_stream(self):
        ui, cmd = self.get_test_ui_and_cmd(options=[('subunit', True)])
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        inserter.status(test_id='failing', test_status='fail')
        inserter.status(test_id='ok', test_status='success')
        inserter.stopTestRun()
        self.assertEqual(0, cmd.execute())
        self.assertEqual(1, len(ui.outputs))
        self.assertEqual('stream', ui.outputs[0][0])
        as_subunit = BytesIO(ui.outputs[0][1])
        stream = ByteStreamToStreamResult(as_subunit)
        log = StreamResult()
        log.startTestRun()
        try:
            stream.run(log)
        finally:
            log.stopTestRun()
        self.assertEqual(
            log._events, [
            ('startTestRun',),
            ('status', 'failing', 'inprogress', None, True, None, None, False,
             None, None, Wildcard),
            ('status', 'failing', 'fail', None, True, None, None, False, None,
             None, Wildcard),
            ('stopTestRun',)
            ])

    def test_with_subunit_no_failures_exit_0(self):
        ui, cmd = self.get_test_ui_and_cmd(options=[('subunit', True)])
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        inserter.status(test_id='ok', test_status='success')
        inserter.stopTestRun()
        self.assertEqual(0, cmd.execute())
        self.assertEqual(1, len(ui.outputs))
        self.assertEqual('stream', ui.outputs[0][0])
        self.assertThat(ui.outputs[0][1], Equals(_b('')))

    def test_with_list_shows_list_of_tests(self):
        ui, cmd = self.get_test_ui_and_cmd(options=[('list', True)])
        cmd.repository_factory = memory.RepositoryFactory()
        repo = cmd.repository_factory.initialise(ui.here)
        inserter = repo.get_inserter()
        inserter.startTestRun()
        inserter.status(test_id='failing1', test_status='fail')
        inserter.status(test_id='ok', test_status='success')
        inserter.status(test_id='failing2', test_status='fail')
        inserter.stopTestRun()
        self.assertEqual(1, cmd.execute(), ui.outputs)
        self.assertEqual(1, len(ui.outputs))
        self.assertEqual('tests_meta', ui.outputs[0][0])
        self.assertEqual(
            {'failing1': {'profiles': []}, 'failing2': {'profiles': []}},
            ui.outputs[0][1])
        self.assertEqual('list', ui.outputs[0][2])

    def test_uses_get_failing(self):
        ui, cmd = self.get_test_ui_and_cmd()
        cmd.repository_factory = memory.RepositoryFactory()
        calls = []
        open = cmd.repository_factory.open
        def decorate_open_with_get_failing(url):
            repo = open(url)
            inserter = repo.get_inserter()
            inserter.startTestRun()
            inserter.status(test_id='failing', test_status='fail')
            inserter.status(test_id='ok', test_status='success')
            inserter.stopTestRun()
            orig = repo.get_failing
            def get_failing():
                calls.append(True)
                return orig()
            repo.get_failing = get_failing
            return repo
        cmd.repository_factory.open = decorate_open_with_get_failing
        cmd.repository_factory.initialise(ui.here)
        self.assertEqual(1, cmd.execute())
        self.assertEqual([True], calls)


class TestFailingConfig(TestFailingBase):
    # Tests that need a config file.

    resources = [('tempdir', TempDirResource())]

    def dirty(self):
        # Ugly: TODO - improve testresources to make this go away.
        dict(self.resources)['tempdir']._dirty = True

    def config_path(self):
        return os.path.join(self.tempdir, '.testr.conf')

    def set_config(self, text):
        self.dirty()
        with open(self.config_path(), 'wt') as stream:
            stream.write(text)

    def test_json(self):
        ui, cmd = self.get_test_ui_and_cmd(options=[('json', True)])
        cmd.repository_factory = memory.RepositoryFactory()
        ui.here = self.tempdir
        repo = cmd.repository_factory.initialise(ui.here)
        ui.proc_outputs=[_b('p1 p2')]
        self.set_config(textwrap.dedent("""\
            [DEFAULT]
            list_profiles=list_profiles
            """))
        inserter = repo.get_inserter(profiles=set(['p1', 'p2']))
        inserter.startTestRun()
        # Fails in both
        inserter.status(
            test_id='t1', test_status='fail', test_tags=set(['p1']))
        inserter.status(
            test_id='t1', test_status='fail', test_tags=set(['p2']))
        # Fails in one
        inserter.status(
            test_id='t2', test_status='fail', test_tags=set(['p1']))
        inserter.status(
            test_id='t2', test_status='success', test_tags=set(['p2']))
        # Only existed in one
        inserter.status(
            test_id='t3', test_status='fail', test_tags=set(['p2']))
        inserter.stopTestRun()
        self.assertEqual(1, cmd.execute(), ui.outputs)
        self.assertEqual([
            ('popen', ('list_profiles',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',),
            ('tests_meta',
             {'t1': {'profiles': ['p1', 'p2']}, 't2': {'profiles': ['p1']},
              't3': {'profiles': ['p2']}},
             'json'),
            ], ui.outputs)
