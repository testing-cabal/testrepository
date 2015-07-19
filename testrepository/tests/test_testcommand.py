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

"""Tests for the testcommand module."""

from __future__ import unicode_literals

from io import BytesIO
import os.path
import optparse
import re

from extras import try_import
import subunit
v2_avail = try_import('subunit.ByteStreamToStreamResult')
from testtools.compat import _b
from testtools.matchers import (
    Equals,
    MatchesAny,
    MatchesException,
    raises,
    )
from testtools.testresult.doubles import ExtendedTestResult

from testrepository.commands import run
from testrepository._computecontext import Instance
from testrepository.ui.model import UI
from testrepository.repository import memory
from testrepository import testcommand
from testrepository.testcommand import TestCommand
from testrepository.tests import ResourcedTestCase, Wildcard
from testrepository.tests.stubpackage import TempDirResource
from testrepository.tests.test_repository import run_timed


class FakeTestCommand(TestCommand):

    def __init__(self, ui, repo):
        TestCommand.__init__(self, ui, repo)
        self.oldschool = True


class TestTestCommand(ResourcedTestCase):

    resources = [('tempdir', TempDirResource())]

    def get_test_ui_and_cmd(self, options=(), args=(), repository=None):
        ui, cmd = self.get_test_ui_and_cmd2(options, args, repository)
        return ui, self.useFixture(cmd)

    def get_test_ui_and_cmd2(self, options=(), args=(), repository=None):
        self.dirty()
        ui = UI(options=options, args=args)
        ui.here = self.tempdir
        return ui, TestCommand(ui, repository)

    def dirty(self):
        # Ugly: TODO - improve testresources to make this go away.
        dict(self.resources)['tempdir']._dirty = True

    def config_path(self):
        return os.path.join(self.tempdir, '.testr.conf')

    def set_config(self, text):
        stream = open(self.config_path(), 'wt')
        try:
            stream.write(text)
        finally:
            stream.close()

    def test_takes_ui(self):
        ui = UI()
        ui.here = self.tempdir
        command = TestCommand(ui, None)
        self.assertEqual(command.ui, ui)

    def test_TestCommand_is_a_fixture(self):
        ui = UI()
        ui.here = self.tempdir
        command = TestCommand(ui, None)
        command.setUp()
        command.cleanUp()

    def test_TestCommand_get_run_command_outside_setUp_fails(self):
        self.dirty()
        ui = UI()
        ui.here = self.tempdir
        command = TestCommand(ui, None)
        self.set_config('[DEFAULT]\ntest_command=foo\n')
        self.assertThat(command.get_run_command, raises(TypeError))
        command.setUp()
        command.cleanUp()
        self.assertThat(command.get_run_command, raises(TypeError))

    def test_TestCommand_cleanUp_disposes_instances(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo\n'
            'instance_dispose=bar $INSTANCE_IDS\n')
        command._instance_cache.add(Instance('DEFAULT', 'baz'))
        command._instance_cache.add(Instance('DEFAULT', 'quux'))
        command.cleanUp()
        command.setUp()
        self.assertEqual([
            ('values', [('running', 'bar baz quux')]),
            ('popen', ('bar baz quux',), {'shell': True}),
            ('communicate',)], ui.outputs)

    def test_TestCommand_cleanUp_disposes_instances_fail_raises(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_results = [1]
        self.set_config(
            '[DEFAULT]\ntest_command=foo\n'
            'instance_dispose=bar $INSTANCE_IDS\n')
        command._instance_cache.add(Instance('DEFAULT', 'baz'))
        command._instance_cache.add(Instance('DEFAULT', 'quux'))
        self.assertThat(command.cleanUp,
            raises(ValueError('Disposing of instances failed, return 1')))
        command.setUp()

    def test_get_run_command_no_config_file_errors(self):
        ui, command = self.get_test_ui_and_cmd()
        self.assertThat(command.get_run_command,
            raises(ValueError('No .testr.conf config file')))

    def test_get_run_command_no_config_settings_errors(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config('')
        self.assertThat(command.get_run_command,
            raises(ValueError(
            'No test_command option present in .testr.conf')))

    def test_get_run_command_returns_fixture_makes_IDFILE(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDOPTION\ntest_id_option=--load-list $IDFILE\n')
        fixture = command.get_run_command(['failing', 'alsofailing'])
        with fixture:
            procs = fixture.run_tests()
            list_file_path = procs[0].list_file_name
            source = open(list_file_path, 'rt')
            try:
                list_file_content = source.read()
            finally:
                source.close()
            procs[0].run_proc.stdout.read()
            procs[0].run_proc.wait()
            self.assertEqual("failing\nalsofailing\n", list_file_content)
        self.assertFalse(os.path.exists(list_file_path))

    def test_get_run_command_IDFILE_variable_setting(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDOPTION\ntest_id_option=--load-list $IDFILE\n')
        fixture = self.useFixture(command.get_run_command(['failing', 'alsofailing']))
        procs = fixture.run_tests()
        expected_cmd = 'foo --load-list %s' % procs[0].list_file_name
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_get_run_command_IDLIST_variable_setting(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n')
        fixture = self.useFixture(
            command.get_run_command(['failing', 'alsofailing']))
        procs = fixture.run_tests()
        expected_cmd = 'foo failing alsofailing'
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_get_run_command_IDLIST_default_is_empty(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n')
        fixture = self.useFixture(command.get_run_command())
        procs = fixture.run_tests()
        expected_cmd = 'foo '
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_get_run_command_default_and_list_expands(self):
        if v2_avail:
            buffer = BytesIO()
            stream = subunit.StreamResultToBytes(buffer)
            stream.status(test_id='returned', test_status='exists')
            stream.status(test_id='ids', test_status='exists')
            subunit_bytes = buffer.getvalue()
        else:
            subunit_bytes = b'returned\nids\n'
        options = optparse.Values()
        options.parallel = True
        options.concurrency = 2
        repo = memory.RepositoryFactory().initialise('memory:')
        ui, command = self.get_test_ui_and_cmd2(repository=repo)
        ui.options = options
        ui.proc_outputs = [subunit_bytes]
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST $LISTOPT\n'
            'test_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        self.useFixture(command)
        fixture = self.useFixture(command.get_run_command())
        del ui.outputs[:]
        procs = fixture.run_tests()
        list(map(lambda x:x.run_proc.wait(), procs))
        self.assertThat(ui.outputs, MatchesAny(
            Equals([
            ('values', [('running', 'foo returned ')]),
            ('popen', ('foo returned ',),
             {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('values', [('running', 'foo ids ')]),
            ('popen', ('foo ids ',),
             {'shell': True, 'stdin': -1, 'stdout': -1})]),
            Equals([
            ('values', [('running', 'foo ids ')]),
            ('popen', ('foo ids ',),
             {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('values', [('running', 'foo returned ')]),
            ('popen', ('foo returned ',),
             {'shell': True, 'stdin': -1, 'stdout': -1})
            ])))

    def test_get_run_command_IDLIST_default_passed_normally(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\ntest_id_list_default=whoo yea\n')
        fixture = self.useFixture(command.get_run_command())
        procs = fixture.run_tests()
        expected_cmd = 'foo whoo yea'
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_IDOPTION_evalutes_empty_string_no_ids(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDOPTION\ntest_id_option=--load-list $IDFILE\n')
        fixture = self.useFixture(command.get_run_command())
        procs = fixture.run_tests()
        expected_cmd = 'foo '
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_group_regex_option(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
                '[DEFAULT]\ntest_command=foo $IDOPTION\n'
                'test_id_option=--load-list $IDFILE\n'
                'group_regex=([^\\.]+\\.)+\n')
        fixture = self.useFixture(command.get_run_command())
        self.assertEqual(
            'pkg.class.', fixture._group_callback('pkg.class.test_method'))

    def test_extra_args_passed_in(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDOPTION\ntest_id_option=--load-list $IDFILE\n')
        fixture = self.useFixture(command.get_run_command(
            testargs=('bar', 'quux')))
        procs = fixture.run_tests()
        expected_cmd = 'foo  bar quux'
        procs[0].run_proc.wait()
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_list_tests_requests_concurrency_instances(self):
        # testr list-tests is non-parallel, so needs 1 instance.
        # testr run triggering list-tests will want to run parallel on all, so
        # avoid latency by asking for whatever concurrency is up front.
        # This covers the case for non-listing runs as well, as the code path
        # is common.
        self.dirty()
        ui = UI(options= [('concurrency', 2), ('parallel', True)])
        ui.here = self.tempdir
        cmd = run.run(ui)
        ui.set_command(cmd)
        ui.proc_outputs = [b'returned\ninstances\n']
        command = self.useFixture(TestCommand(ui, None))
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n'
            'instance_provision=provision -c $INSTANCE_COUNT\n'
            'instance_execute=quux $INSTANCE_ID -- $COMMAND\n')
        fixture = self.useFixture(command.get_run_command(test_ids=['1']))
        fixture.list_tests()
        self.assertEqual(2, command._instance_cache.size())
        # Little ugly. We can allocate two, as the list used and released one.
        command._instance_cache.allocate('DEFAULT')
        command._instance_cache.allocate('DEFAULT')
        self.assertThat(ui.outputs, MatchesAny(Equals([
            ('values', [('running', 'provision -c 2')]),
            ('popen', ('provision -c 2',), {'shell': True, 'stdout': -1}),
            ('communicate',),
            ('values', [('running', 'quux instances -- foo --list whoo yea')]),
            ('popen',('quux instances -- foo --list whoo yea',),
             {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)]), Equals([
            ('values', [('running', 'provision -c 2')]),
            ('popen', ('provision -c 2',), {'shell': True, 'stdout': -1}),
            ('communicate',),
            ('values', [('running', 'quux returned -- foo --list whoo yea')]),
            ('popen',('quux returned -- foo --list whoo yea',),
             {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)])))

    def test_list_tests_uses_instances(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n'
            'instance_execute=quux $INSTANCE_ID -- $COMMAND\n')
        fixture = self.useFixture(command.get_run_command())
        command._instance_cache.add(Instance('DEFAULT', 'bar'))
        fixture.list_tests()
        self.assertEqual(1, command._instance_cache.size())
        self.assertEqual(
            Instance('DEFAULT', 'bar'), command._instance_cache.allocate('DEFAULT'))
        self.assertEqual([
            ('values', [('running', 'quux bar -- foo --list whoo yea')]),
            ('popen', ('quux bar -- foo --list whoo yea',),
             {'shell': True, 'stdin': -1, 'stdout': -1}), ('communicate',)],
            ui.outputs)

    def test_list_tests_cmd(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        fixture = self.useFixture(command.get_run_command())
        expected_cmd = 'foo --list whoo yea'
        self.assertEqual(expected_cmd, fixture.list_cmd)

    def test_list_tests_parsing(self):
        if v2_avail:
            buffer = BytesIO()
            stream = subunit.StreamResultToBytes(buffer)
            stream.status(test_id='returned', test_status='exists')
            stream.status(test_id='ids', test_status='exists')
            subunit_bytes = buffer.getvalue()
        else:
            subunit_bytes = b'returned\nids\n'
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [subunit_bytes]
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        fixture = self.useFixture(command.get_run_command())
        self.assertEqual(set(['returned', 'ids']), set(fixture.list_tests()))

    def test_list_tests_nonzero_exit(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_results = [1]
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        fixture = self.useFixture(command.get_run_command())
        self.assertThat(lambda:fixture.list_tests(), raises(ValueError))

    def test_partition_tests_smoke(self):
        repo = memory.RepositoryFactory().initialise('memory:')
        # Seed with 1 slow and 2 tests making up 2/3 the time.
        result = repo.get_inserter()
        result.startTestRun()
        run_timed("slow", 3, result)
        run_timed("fast1", 1, result)
        run_timed("fast2", 1, result)
        result.stopTestRun()
        ui, command = self.get_test_ui_and_cmd(repository=repo)
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST $LISTOPT\n'
            'test_list_option=--list\n')
        fixture = self.useFixture(command.get_run_command())
        # partitioning by two generates 'slow' and the two fast ones as partitions
        # flushed out by equal numbers of unknown duration tests.
        test_ids = frozenset(['slow', 'fast1', 'fast2', 'unknown1', 'unknown2',
            'unknown3', 'unknown4'])
        partitions = fixture.partition_tests(test_ids, 2)
        self.assertTrue('slow' in partitions[0])
        self.assertFalse('fast1' in partitions[0])
        self.assertFalse('fast2' in partitions[0])
        self.assertFalse('slow' in partitions[1])
        self.assertTrue('fast1' in partitions[1])
        self.assertTrue('fast2' in partitions[1])
        self.assertEqual(3, len(partitions[0]))
        self.assertEqual(4, len(partitions[1]))

    def test_partition_tests_914359(self):
        # When two partitions have the same duration, timed tests should be
        # appended to the shortest partition. In theory this doesn't matter,
        # but in practice, if a test is recorded with 0 duration (e.g. due to a
        # bug), it is better to have them split out rather than all in one
        # partition. 0 duration tests are unlikely to really be 0 duration.
        repo = memory.RepositoryFactory().initialise('memory:')
        # Seed with two 0-duration tests.
        result = repo.get_inserter()
        result.startTestRun()
        run_timed("zero1", 0, result)
        run_timed("zero2", 0, result)
        result.stopTestRun()
        ui, command = self.get_test_ui_and_cmd(repository=repo)
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n')
        fixture = self.useFixture(command.get_run_command())
        # partitioning by two should generate two one-entry partitions.
        test_ids = frozenset(['zero1', 'zero2'])
        partitions = fixture.partition_tests(test_ids, 2)
        self.assertEqual(1, len(partitions[0]))
        self.assertEqual(1, len(partitions[1]))

    def test_partition_tests_with_grouping(self):
        repo = memory.RepositoryFactory().initialise('memory:')
        result = repo.get_inserter()
        result.startTestRun()
        run_timed("TestCase1.slow", 3, result)
        run_timed("TestCase2.fast1", 1, result)
        run_timed("TestCase2.fast2", 1, result)
        result.stopTestRun()
        ui, command = self.get_test_ui_and_cmd(repository=repo)
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST $LISTOPT\n'
            'test_list_option=--list\n')
        fixture = self.useFixture(command.get_run_command())
        test_ids = frozenset(['TestCase1.slow', 'TestCase1.fast',
                              'TestCase1.fast2', 'TestCase2.fast1',
                              'TestCase3.test1', 'TestCase3.test2',
                              'TestCase2.fast2', 'TestCase4.test',
                              'testdir.testfile.TestCase5.test'])
        regex = 'TestCase[0-5]'
        def group_id(test_id, regex=re.compile('TestCase[0-5]')):
            match = regex.match(test_id)
            if match:
                return match.group(0)
        # There isn't a public way to define a group callback [as yet].
        fixture._group_callback = group_id
        partitions = fixture.partition_tests(test_ids, 2)
        # Timed groups are deterministic:
        self.assertTrue('TestCase2.fast1' in partitions[0])
        self.assertTrue('TestCase2.fast2' in partitions[0])
        self.assertTrue('TestCase1.slow' in partitions[1])
        self.assertTrue('TestCase1.fast' in partitions[1])
        self.assertTrue('TestCase1.fast2' in partitions[1])
        # Untimed groups just need to be kept together:
        if 'TestCase3.test1' in partitions[0]:
            self.assertTrue('TestCase3.test2' in partitions[0])
        if 'TestCase4.test' not in partitions[0]:
            self.assertTrue('TestCase4.test' in partitions[1])
        if 'testdir.testfile.TestCase5.test' not in partitions[0]:
            self.assertTrue('testdir.testfile.TestCase5.test' in partitions[1])

    def test_run_tests_with_instances(self):
        # when there are instances and no instance_execute, run_tests acts as
        # normal.
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n')
        command._instance_cache.add(Instance('DEFAULT', 'foo'))
        command._instance_cache.add(Instance('DEFAULT', 'bar'))
        fixture = self.useFixture(command.get_run_command())
        procs = fixture.run_tests()
        self.assertEqual([
            ('values', [('running', 'foo ')]),
            ('popen', ('foo ',), {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)

    def test_run_tests_with_existing_instances_configured(self):
        # when there are instances present, they are pulled out for running
        # tests.
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n'
            'instance_execute=quux $INSTANCE_ID -- $COMMAND\n')
        command._instance_cache.add(Instance('DEFAULT', 'bar'))
        fixture = self.useFixture(command.get_run_command(test_ids=['1']))
        procs = fixture.run_tests()
        self.assertEqual([
            ('values', [('running', 'quux bar -- foo 1')]),
            ('popen', ('quux bar -- foo 1',),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)
        # No --parallel, so the one instance should have been allocated.
        self.assertEqual(1, command._instance_cache.size())
        self.assertRaises(KeyError, command._instance_cache.allocate, 'DEFAULT')
        # And after the process is run, bar is returned for re-use.
        procs[0].run_proc.stdout.read()
        procs[0].run_proc.wait()
        self.assertEqual(0, procs[0].run_proc.returncode)
        self.assertEqual(1, command._instance_cache.size())
        command._instance_cache.allocate('DEFAULT')

    def test_run_tests_allocated_instances_skipped(self):
        repo = memory.RepositoryFactory().initialise('memory:')
        ui, command = self.get_test_ui_and_cmd(repository=repo)
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDLIST\n'
            'instance_execute=quux $INSTANCE_ID -- $COMMAND\n')
        command._instance_cache.add(Instance('DEFAULT', 'baz'))
        command._instance_cache.allocate('DEFAULT')
        command._instance_cache.add(Instance('DEFAULT', 'bar'))
        fixture = self.useFixture(command.get_run_command(test_ids=['1']))
        procs = fixture.run_tests()
        self.assertEqual([
            ('values', [('running', 'quux bar -- foo 1')]),
            ('popen', ('quux bar -- foo 1',),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)
        # No --parallel, so the one instance should have been allocated.
        self.assertEqual(2, command._instance_cache.size())
        self.assertRaises(KeyError, command._instance_cache.allocate, 'DEFAULT')
        # And after the process is run, bar is returned for re-use.
        procs[0].run_proc.wait()
        procs[0].run_proc.stdout.read()
        self.assertEqual(0, procs[0].run_proc.returncode)
        self.assertEqual(2, command._instance_cache.size())
        self.assertEqual(Instance('DEFAULT', 'bar'), command._instance_cache.allocate('DEFAULT'))
        self.assertRaises(KeyError, command._instance_cache.allocate, 'DEFAULT')

    def test_run_tests_list_file_in_FILES(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\ntest_command=foo $IDFILE\n'
            'instance_execute=quux $INSTANCE_ID $FILES -- $COMMAND\n')
        command._instance_cache.add(Instance('DEFAULT', 'bar'))
        fixture = self.useFixture(command.get_run_command(test_ids=['1']))
        procs = fixture.run_tests()
        list_file = procs[0].list_file_name
        expected_cmd = 'quux bar %s -- foo %s' % (list_file, list_file)
        self.assertEqual([
            ('values', [('running', expected_cmd)]),
            ('popen', (expected_cmd,),
             {'shell': True, 'stdin': -1, 'stdout': -1})],
            ui.outputs)
        # No --parallel, so the one instance should have been allocated.
        self.assertEqual(1, command._instance_cache.size())
        self.assertRaises(KeyError, command._instance_cache.allocate, 'DEFAULT')
        # And after the process is run, bar is returned for re-use.
        procs[0].run_proc.stdout.read()
        procs[0].run_proc.wait()
        self.assertEqual(0, procs[0].run_proc.returncode)
        self.assertEqual(1, command._instance_cache.size())
        command._instance_cache.allocate('DEFAULT')

    def test_filter_tags_parsing(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config('[DEFAULT]\nfilter_tags=foo bar\n')
        self.assertEqual(set(['foo', 'bar']), command.get_filter_tags())

    def test_callout_concurrency(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [b'4']
        self.set_config(
            '[DEFAULT]\ntest_run_concurrency=probe\n'
            'test_command=foo\n')
        self.assertEqual(
            4, testcommand._callout_concurrency(command.get_parser(), ui))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_callout_concurrency_failed(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_results = [1]
        self.set_config(
            '[DEFAULT]\ntest_run_concurrency=probe\n'
            'test_command=foo\n')
        self.assertThat(
            lambda:testcommand._callout_concurrency(command.get_parser(), ui),
            raises(ValueError(
                "test_run_concurrency failed: exit code 1, stderr=''")))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_callout_concurrency_not_set(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\n'
            'test_command=foo\n')
        self.assertEqual(
            None, testcommand._callout_concurrency(command.get_parser(), ui))
        self.assertEqual([], ui.outputs)

    def test_default_profiles(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [b'py27 py34']
        self.set_config(
            '[DEFAULT]\ndefault_profiles=probe\n'
            'test_command=foo\n')
        self.assertEqual(
            set(['py27', 'py34']),
            testcommand._default_profiles(command.get_parser(), ui))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_default_profiles_failed(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_results = [1]
        self.set_config(
            '[DEFAULT]\ndefault_profiles=probe\n'
            'test_command=foo\n')
        self.assertThat(lambda:testcommand._default_profiles(
            command.get_parser(), ui), raises(
            ValueError("default_profiles failed: exit code 1, stderr=''")))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_default_profiles_not_set(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\n'
            'test_command=foo\n')
        self.assertEqual(
            set(),
            testcommand._default_profiles(command.get_parser(), ui))
        self.assertEqual([], ui.outputs)

    def test_list_profiles(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [b'py27 py34']
        self.set_config(
            '[DEFAULT]\nlist_profiles=probe\n'
            'test_command=foo\n')
        self.assertEqual(
            set(['py27', 'py34']),
            testcommand._list_profiles(command.get_parser(), ui))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_list_profiles_failed(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_results = [1]
        self.set_config(
            '[DEFAULT]\nlist_profiles=probe\n'
            'test_command=foo\n')
        self.assertThat(lambda:testcommand._list_profiles(
            command.get_parser(), ui), raises(
            ValueError("list_profiles failed: exit code 1, stderr=''")))
        self.assertEqual([
            ('popen', ('probe',), {'shell': True, 'stdin': -1, 'stdout': -1}),
            ('communicate',)], ui.outputs)

    def test_list_profiles_not_set(self):
        ui, command = self.get_test_ui_and_cmd()
        self.set_config(
            '[DEFAULT]\n'
            'test_command=foo\n')
        self.assertEqual(
            set(),
            testcommand._list_profiles(command.get_parser(), ui))
        self.assertEqual([], ui.outputs)

    def test_filter_tests_by_regex_only(self):
        if v2_avail:
            buffer = BytesIO()
            stream = subunit.StreamResultToBytes(buffer)
            stream.status(test_id='returned', test_status='exists')
            stream.status(test_id='ids', test_status='exists')
            subunit_bytes = buffer.getvalue()
        else:
            subunit_bytes = b'returned\nids\n'
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [subunit_bytes]
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        filters = ['return']
        fixture = self.useFixture(command.get_run_command(test_filters=filters))
        self.assertEqual(['returned'], fixture.test_ids)

    def test_filter_tests_by_regex_supplied_ids(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [b'returned\nids\n']
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        filters = ['return']
        fixture = self.useFixture(command.get_run_command(
            test_ids=['return', 'of', 'the', 'king'], test_filters=filters))
        self.assertEqual(['return'], fixture.test_ids)

    def test_filter_tests_by_regex_supplied_ids_multi_match(self):
        ui, command = self.get_test_ui_and_cmd()
        ui.proc_outputs = [b'returned\nids\n']
        self.set_config(
            '[DEFAULT]\ntest_command=foo $LISTOPT $IDLIST\ntest_id_list_default=whoo yea\n'
            'test_list_option=--list\n')
        filters = ['return']
        fixture = self.useFixture(command.get_run_command(
            test_ids=['return', 'of', 'the', 'king', 'thereisnoreturn'], test_filters=filters))
        self.assertEqual(['return', 'thereisnoreturn'], fixture.test_ids)
