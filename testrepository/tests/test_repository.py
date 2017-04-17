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

"""Tests for Repository support logic and the Repository contract."""

from datetime import (
    datetime,
    timedelta,
    )
import doctest

from subunit import (
    iso8601,
    v2,
    )

from testresources import TestResource
from testtools import (
    clone_test_with_new_id,
    content,
    PlaceHolder,
    )
import testtools
from testtools.compat import _b
from testtools.testresult.doubles import (
    ExtendedTestResult,
    StreamResult,
    )
from testtools.matchers import DocTestMatches, raises

from testrepository import repository
from testrepository.repository import file, memory
from testrepository.tests import (
    ResourcedTestCase,
    Wildcard,
    )
from testrepository.tests.stubpackage import (
    TempDirResource,
    )


class RecordingRepositoryFactory(object):
    """Test helper for tests wanting to check repository factory callers."""

    def __init__(self, calls, decorated):
        self.calls = calls
        self.factory = decorated

    def initialise(self, url):
        self.calls.append(('initialise', url))
        return self.factory.initialise(url)

    def open(self, url):
        self.calls.append(('open', url))
        return self.factory.open(url)


class DirtyTempDirResource(TempDirResource):

    def __init__(self):
        TempDirResource.__init__(self)
        self._dirty = True

    def isDirty(self):
        return True

    def _setResource(self, new_resource):
        """Set the current resource to a new value."""
        self._currentResource = new_resource
        self._dirty = True


class MemoryRepositoryFactoryResource(TestResource):

    def make(self, dependency_resources):
        return memory.RepositoryFactory()


# what repository implementations do we need to test?
repo_implementations = [
    ('file', {'repo_impl': file.RepositoryFactory(),
        'resources': [('sample_url', DirtyTempDirResource())]
        }),
    ('memory', {
        'resources': [('repo_impl', MemoryRepositoryFactoryResource())],
        'sample_url': 'memory:'}),
    ]


class Case(ResourcedTestCase):
    """Reference tests."""

    def passing(self):
        pass

    def unexpected_success(self):
        self.expectFailure("unexpected success", self.assertTrue, True)


class FailingCase:

    def run(self, result):
        result.startTest(self)
        result.addError(
            self, None, details={'traceback': content.text_content("")})
        result.stopTest(self)

def make_test(id, should_pass):
    """Make a test."""
    if should_pass:
        case = Case("passing")
    else:
        case = FailingCase()
    return clone_test_with_new_id(case, id)


def run_timed(id, duration, result, enumeration=False):
    """Make and run a test taking duration seconds.
    
    :param enumeration: If True, don't run, just enumerate.
    """
    start = datetime.now(tz=iso8601.Utc())
    if enumeration:
        result.status(test_id=id, test_status='exists', timestamp=start)
    else:
        result.status(test_id=id, test_status='inprogress', timestamp=start)
        result.status(test_id=id, test_status='success',
            timestamp=start + timedelta(seconds=duration))


class TestRepositoryErrors(ResourcedTestCase):

    def test_not_found(self):
        url = 'doesntexistatall'
        error = repository.RepositoryNotFound(url)
        self.assertEqual(
            'No repository found in %s. Create one by running "testr init".'
            % url, str(error))


class TestRepositoryContract(ResourcedTestCase):

    scenarios = repo_implementations

    def get_failing(self, repo):
        """Analyze a failing stream from repo and return it."""
        run = repo.get_failing()
        analyzer = testtools.StreamSummary()
        analyzer.startTestRun()
        try:
            run.get_test().run(analyzer)
        finally:
            analyzer.stopTestRun()
        return analyzer

    def get_failing_list(self, repo):
        """Analyze a failing stream from repo and return test dicts for it."""
        run = repo.get_failing()
        analyzed = []
        analyzer = testtools.StreamToDict(on_test=analyzed.append)
        analyzer.startTestRun()
        try:
            run.get_test().run(analyzer)
        finally:
            analyzer.stopTestRun()
        return analyzed

    def get_last_run(self, repo):
        """Return the results from a stream."""
        run = repo.get_test_run(repo.latest_id())
        analyzer = testtools.StreamSummary()
        analyzer.startTestRun()
        try:
            run.get_test().run(analyzer)
        finally:
            analyzer.stopTestRun()
        return analyzer

    def test_can_initialise_with_param(self):
        repo = self.repo_impl.initialise(self.sample_url)
        self.assertIsInstance(repo, repository.AbstractRepository)

    def test_can_get_inserter_no_args(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        self.assertNotEqual(None, result)

    def test_can_get_inserter_profiles(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter(profiles=['DEFAULT'])
        self.assertNotEqual(None, result)

    def test_insert_stream_smoke(self):
        # We can insert some data into the repository.
        repo = self.repo_impl.initialise(self.sample_url)
        class Case(ResourcedTestCase):
            def method(self):
                pass
        case = Case('method')
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        case.run(legacy_result)
        legacy_result.stopTestRun()
        self.assertEqual(1, repo.count())
        self.assertNotEqual(None, result.get_id())

    def test_open(self):
        self.repo_impl.initialise(self.sample_url)
        self.repo_impl.open(self.sample_url)

    def test_open_non_existent(self):
        url = 'doesntexistatall'
        self.assertThat(lambda: self.repo_impl.open(url),
            raises(repository.RepositoryNotFound(url)))

    def test_inserting_creates_id(self):
        # When inserting a stream, an id is returned from stopTestRun.
        # Note that this is no longer recommended - but kept for compatibility.
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        self.assertNotEqual(None, result.stopTestRun())

    def test_count(self):
        repo = self.repo_impl.initialise(self.sample_url)
        self.assertEqual(0, repo.count())
        result = repo.get_inserter()
        result.startTestRun()
        result.stopTestRun()
        self.assertEqual(1, repo.count())
        result = repo.get_inserter()
        result.startTestRun()
        result.stopTestRun()
        self.assertEqual(2, repo.count())

    def test_latest_id_empty(self):
        repo = self.repo_impl.initialise(self.sample_url)
        self.assertThat(repo.latest_id,
            raises(KeyError("No tests in repository")))

    def test_latest_id_nonempty(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        result.stopTestRun()
        inserted = result.get_id()
        self.assertEqual(inserted, repo.latest_id())

    def test_get_failing_empty(self):
        # repositories can return a TestRun with just latest failures in it.
        repo = self.repo_impl.initialise(self.sample_url)
        analyzed = self.get_failing(repo)
        self.assertEqual(0, analyzed.testsRun)

    def test_get_failing_one_run(self):
        # repositories can return a TestRun with just latest failures in it.
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('passing', True).run(legacy_result)
        make_test('failing', False).run(legacy_result)
        legacy_result.stopTestRun()
        analyzed = self.get_failing(repo)
        self.assertEqual(1, analyzed.testsRun)
        self.assertEqual(1, len(analyzed.errors))
        self.assertEqual('failing', analyzed.errors[0][0].id())

    def test_unexpected_success(self):
        # Unexpected successes get forwarded too. (Test added because of a
        # NameError in memory repo).
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        test = clone_test_with_new_id(Case('unexpected_success'), 'unexpected_success')
        test.run(legacy_result)
        legacy_result.stopTestRun()
        analyzed = self.get_last_run(repo)
        self.assertEqual(1, analyzed.testsRun)
        self.assertEqual(1, len(analyzed.unexpectedSuccesses))
        self.assertEqual('unexpected_success', analyzed.unexpectedSuccesses[0].id())

    def test_get_failing_complete_runs_delete_missing_failures(self):
        # failures from complete runs replace all failures.
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('passing', True).run(legacy_result)
        make_test('failing', False).run(legacy_result)
        make_test('missing', False).run(legacy_result)
        legacy_result.stopTestRun()
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('passing', False).run(legacy_result)
        make_test('failing', True).run(legacy_result)
        legacy_result.stopTestRun()
        analyzed = self.get_failing(repo)
        self.assertEqual(1, analyzed.testsRun)
        self.assertEqual(1, len(analyzed.errors))
        self.assertEqual('passing', analyzed.errors[0][0].id())

    def test_get_failing_partial_runs_preserve_missing_failures(self):
        # failures from two runs add to existing failures, and successes remove
        # from them.
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('passing', True).run(legacy_result)
        make_test('failing', False).run(legacy_result)
        make_test('missing', False).run(legacy_result)
        legacy_result.stopTestRun()
        result = repo.get_inserter(partial=True)
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('passing', False).run(legacy_result)
        make_test('failing', True).run(legacy_result)
        legacy_result.stopTestRun()
        analyzed = self.get_failing(repo)
        self.assertEqual(2, analyzed.testsRun)
        self.assertEqual(2, len(analyzed.errors))
        self.assertEqual(set(['passing', 'missing']),
            set([test[0].id() for test in analyzed.errors]))

    def test_get_test_run_missing_keyerror(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        result.stopTestRun()
        inserted = result.get_id()
        self.assertThat(lambda:repo.get_test_run(inserted - 1),
            raises(KeyError))

    def test_get_test_run(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        inserted = result.stopTestRun()
        run = repo.get_test_run(inserted)
        self.assertNotEqual(None, run)

    def test_get_latest_run(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        inserted = result.stopTestRun()
        run = repo.get_latest_run()
        self.assertEqual(inserted, run.get_id())

    def test_get_latest_run_empty_repo(self):
        repo = self.repo_impl.initialise(self.sample_url)
        self.assertRaises(KeyError, repo.get_latest_run)

    def test_get_test_run_get_id(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        inserted = result.stopTestRun()
        run = repo.get_test_run(inserted)
        self.assertEqual(inserted, run.get_id())

    def test_get_test_run_preserves_time(self):
        self.skip('Fix me before releasing.')
        # The test run outputs the time events that it received.
        now = datetime(2001, 1, 1, 0, 0, 0, tzinfo=iso8601.Utc())
        second = timedelta(seconds=1)
        repo = self.repo_impl.initialise(self.sample_url)
        test_id = self.getUniqueString()
        test = make_test(test_id, True)
        result = repo.get_inserter()
        result.startTestRun()
        result.status(timestamp=now, test_id=test_id, test_status='inprogress')
        result.status(timestamp=(now + 1 * second), test_id=test_id, test_status='success')
        inserted = result.stopTestRun()
        run = repo.get_test_run(inserted)
        result = ExtendedTestResult()
        run.get_test().run(result)
        self.assertEqual(
            [('time', now),
             ('tags', set(), set()),
             ('startTest', Wildcard),
             ('time', now + 1 * second),
             ('addSuccess', Wildcard),
             ('stopTest', Wildcard),
             ('tags', set(), set()),
             ],
            result._events)

    def test_get_failing_get_id(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        result.startTestRun()
        result.stopTestRun()
        run = repo.get_failing()
        self.assertEqual(None, run.get_id())

    def test_get_failing_get_subunit_stream(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('testrepository.tests.test_repository.Case.method', False).run(legacy_result)
        legacy_result.stopTestRun()
        run = repo.get_failing()
        as_subunit = run.get_subunit_stream()
        stream = v2.ByteStreamToStreamResult(as_subunit)
        log = StreamResult()
        log.startTestRun()
        try:
            stream.run(log)
        finally:
            log.stopTestRun()
        self.assertEqual(
            log._events, [
            ('startTestRun',),
            ('status',
             'testrepository.tests.test_repository.Case.method',
             'inprogress',
             None,
             True,
             None,
             None,
             False,
             None,
             None,
             Wildcard),
            ('status',
             'testrepository.tests.test_repository.Case.method',
             None,
             None,
             True,
             'traceback',
             Wildcard,
             True,
             Wildcard,
             None,
             Wildcard),
            ('status',
             'testrepository.tests.test_repository.Case.method',
             'fail',
             None,
             True,
             None,
             None,
             False,
             None,
             None,
             Wildcard),
            ('stopTestRun',)
            ])

    def test_get_subunit_from_test_run(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('testrepository.tests.test_repository.Case.method', True).run(legacy_result)
        legacy_result.stopTestRun()
        inserted = result.get_id()
        run = repo.get_test_run(inserted)
        as_subunit = run.get_subunit_stream()
        stream = v2.ByteStreamToStreamResult(as_subunit)
        log = StreamResult()
        log.startTestRun()
        try:
            stream.run(log)
        finally:
            log.stopTestRun()
        self.assertEqual(
            log._events,
            [
            ('startTestRun',),
            ('status',
             'testrepository.tests.test_repository.Case.method',
             'inprogress',
             None,
             True,
             None,
             None,
             False,
             None,
             None,
             Wildcard),
            ('status',
             'testrepository.tests.test_repository.Case.method',
             'success',
             None,
             True,
             None,
             None,
             False,
             None,
             None,
             Wildcard),
            ('stopTestRun',)
            ])

    def test_get_test_from_test_run(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        make_test('testrepository.tests.test_repository.Case.method', True).run(legacy_result)
        legacy_result.stopTestRun()
        inserted = result.get_id()
        run = repo.get_test_run(inserted)
        test = run.get_test()
        result = testtools.StreamSummary()
        result.startTestRun()
        try:
            test.run(result)
        finally:
            result.stopTestRun()
        self.assertEqual(1, result.testsRun)

    def test_get_times_unknown_tests_are_unknown(self):
        repo = self.repo_impl.initialise(self.sample_url)
        test_ids = set(['foo', 'bar'])
        self.assertEqual(test_ids, repo.get_test_times(test_ids)['unknown'])

    def test_inserted_test_times_known(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        test_name = 'testrepository.tests.test_repository.Case.method'
        run_timed(test_name, 0.1, legacy_result)
        legacy_result.stopTestRun()
        self.assertEqual({test_name: 0.1},
            repo.get_test_times([test_name])['known'])

    def test_inserted_exists_no_impact_on_test_times(self):
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(result)
        legacy_result.startTestRun()
        test_name = 'testrepository.tests.test_repository.Case.method'
        run_timed(test_name, 0.1, legacy_result)
        legacy_result.stopTestRun()
        result = repo.get_inserter()
        result.startTestRun()
        test_name = 'testrepository.tests.test_repository.Case.method'
        run_timed(test_name, 0.2, result, True)
        result.stopTestRun()
        self.assertEqual({test_name: 0.1},
            repo.get_test_times([test_name])['known'])

    def test_get_test_ids(self):
        repo = self.repo_impl.initialise(self.sample_url)
        inserter = repo.get_inserter()
        legacy_result = testtools.ExtendedToStreamDecorator(inserter)
        legacy_result.startTestRun()
        test_cases = [PlaceHolder(self.getUniqueString()) for r in range(5)]
        for test_case in test_cases:
            test_case.run(legacy_result)
        legacy_result.stopTestRun()
        run_id = inserter.get_id()
        self.assertEqual(run_id, repo.latest_id())
        returned_ids = repo.get_test_ids(run_id)
        self.assertEqual([test.id() for test in test_cases], returned_ids)

    def test_insert_multiple_profiles_sets_failing(self):
        # If a single run has the same test multiple times in different
        # profiles, the failures are captured and reported even if
        # successes are signaled after that.
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter(profiles=set(['p1', 'p2', 'p3']))
        result.startTestRun()
        now = datetime.now(tz=iso8601.Utc())
        result.status(
            test_id='testid', test_tags=set(['p1']), test_status='success',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p2']), test_status='fail',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p3']), test_status='success',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        # Note - this fails sporadically on pypy3 w/file repo on a differing
        # microsecond! (Odd with a fixed timestamp, but there you are) - I
        # think the migration of the repo to v2 will fix this, thus tolerating
        # it for now.
        self.assertEqual([{'details': {},
            'id': 'testid',
            'status': 'fail',
            'tags': set(['p2']),
            'timestamps': [now, now]}], analyzed)

    def test_insert_multiple_profiles_partial_updates(self):
        # If a single run has the same test multiple times in different
        # profiles, the failures are captured and reported distinctly.
        # p1, p2 fail
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter(profiles=set(['p1', 'p2', 'p3']))
        result.startTestRun()
        now = datetime.now(tz=iso8601.Utc())
        result.status(
            test_id='testid', test_tags=set(['p1']), test_status='fail',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p2']), test_status='fail',
            timestamp=now)
        result.stopTestRun()
        # Now p1 is missing (and should carry through),
        # p2 succeeds (and should no longer be reported failing)
        # and p3 is a new failure and should be reported failing
        result = repo.get_inserter(
            partial=True, profiles=set(['p1', 'p2', 'p3']))
        result.startTestRun()
        result.status(
            test_id='testid', test_tags=set(['p2']), test_status='success',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p3']), test_status='fail',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        analyzed.sort(key=lambda d:list(d['tags']))
        self.assertEqual([
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p1']),
             'timestamps': [now, now]},
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p3']),
             'timestamps': [now, now]},
            ], analyzed)

    def test_insert_missing_profile_does_not_reset_other_failing_test(self):
        # Only the supplied profiles are considered, not arbitrary tags
        # (otherwise worker-N tags would cause failures to be considered
        # distinct).
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter(profiles=set(['p1', 'p2', 'p3']))
        result.startTestRun()
        now = datetime.now(tz=iso8601.Utc())
        # These two should be considered identical
        result.status(
            test_id='testid', test_tags=set(['p1', 't1']), test_status='fail',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p1', 't2']), test_status='fail',
            timestamp=now)

        result.stopTestRun()
        # Now p1 is missing (and should carry through),
        # p2 succeeds (and should no longer be reported failing)
        # and p3 is a new failure and should be reported failing
        result = repo.get_inserter(
            partial=True, profiles=set(['p1', 'p2', 'p3']))
        result.startTestRun()
        result.status(
            test_id='testid', test_tags=set(['p2']), test_status='success',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p3']), test_status='fail',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        analyzed.sort(key=lambda d:sorted(d['tags']))
        self.assertEqual([
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p1', 't2']),
             'timestamps': [now, now]},
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p3']),
             'timestamps': [now, now]},
            ], analyzed)

    def test_insert_non_profile_tags_ignored_for_failing_deduplication(self):
        # Only the supplied profiles are considered, not arbitrary tags
        # (otherwise worker-N tags would cause failures to be considered
        # distinct).
        repo = self.repo_impl.initialise(self.sample_url)
        result = repo.get_inserter(profiles=['p1'])
        result.startTestRun()
        now = datetime.now(tz=iso8601.Utc())
        # These two should be considered identical
        result.status(
            test_id='testid', test_tags=set(['p1', 't1']), test_status='fail',
            timestamp=now)
        result.status(
            test_id='testid', test_tags=set(['p1', 't2']), test_status='fail',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        self.assertEqual([
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p1', 't2']), # The most recent one wins
             'timestamps': [now, now]},
            ], analyzed)
        # On updates this applies too
        result = repo.get_inserter(partial=True, profiles=['p1'])
        result.startTestRun()
        result.status(
            test_id='testid', test_tags=set(['p1']), test_status='fail',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        self.assertEqual([
            {'details': {},
             'id': 'testid',
             'status': 'fail',
             'tags': set(['p1']),
             'timestamps': [now, now]},
            ], analyzed)
        # Including fail -> success transitions.
        result = repo.get_inserter(partial=True, profiles=['p1'])
        result.startTestRun()
        result.status(
            test_id='testid', test_tags=set(['p1']), test_status='success',
            timestamp=now)
        result.stopTestRun()
        analyzed = self.get_failing_list(repo)
        self.assertEqual([], analyzed)
