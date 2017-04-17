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

"""In memory storage of test results."""

from extras import try_import

OrderedDict = try_import('collections.OrderedDict', dict)
from io import BytesIO
from operator import methodcaller

import subunit
import testtools

from testrepository.repository import (
    AbstractRepository,
    AbstractRepositoryFactory,
    AbstractTestRun,
    RepositoryNotFound,
    )


class RepositoryFactory(AbstractRepositoryFactory):
    """A factory that can initialise and open memory repositories.

    This is used for testing where a repository may be created and later
    opened, but tests should not see each others repositories.
    """

    def __init__(self):
        self.repos = {}

    def initialise(self, url):
        self.repos[url] = Repository()
        return self.repos[url]

    def open(self, url):
        try:
            return self.repos[url]
        except KeyError:
            raise RepositoryNotFound(url)


class Repository(AbstractRepository):
    """In memory storage of test results."""

    def __init__(self):
        # Test runs:
        self._runs = []
        self._failing = OrderedDict() # (id, profiles) -> test
        self._times = {} # id -> duration

    def count(self):
        return len(self._runs)

    def get_failing(self):
        return _Failures(self)

    def get_test_run(self, run_id):
        if run_id < 0:
            raise KeyError("No such run.")
        return self._runs[run_id]

    def latest_id(self):
        result = self.count() - 1
        if result < 0:
            raise KeyError("No tests in repository")
        return result

    def _get_inserter(self, partial, profiles):
        return _Inserter(self, partial, profiles)

    def _get_test_times(self, test_ids):
        result = {}
        for test_id in test_ids:
            duration = self._times.get(test_id, None)
            if duration is not None:
                result[test_id] = duration
        return result


# XXX: Too much duplication between this and _Inserter
class _Failures(AbstractTestRun):
    """Report on failures from a memory repository."""

    def __init__(self, repository):
        self._repository = repository

    def get_id(self):
        return None

    def get_subunit_stream(self):
        result = BytesIO()
        serialiser = subunit.v2.StreamResultToBytes(result)
        serialiser = testtools.ExtendedToStreamDecorator(serialiser)
        serialiser.startTestRun()
        try:
            self.run(serialiser)
        finally:
            serialiser.stopTestRun()
        result.seek(0)
        return result

    def get_test(self):
        def wrap_result(result):
            # Wrap in a router to mask out startTestRun/stopTestRun from the
            # ExtendedToStreamDecorator.
            result = testtools.StreamResultRouter(result, do_start_stop_run=False)
            # Wrap that in ExtendedToStreamDecorator to convert v1 calls to
            # StreamResult.
            return testtools.ExtendedToStreamDecorator(result)
        return testtools.DecorateTestCaseResult(
            self, wrap_result, methodcaller('startTestRun'),
            methodcaller('stopTestRun'))

    def run(self, result):
        # Speaks original V1 protocol.
        for case in self._repository._failing.values():
            case.run(result)


class _Inserter(AbstractTestRun):
    """Insert test results into a memory repository, and describe them later."""

    def __init__(self, repository, partial, profiles):
        self._repository = repository
        self._partial = partial
        self._profiles = set(profiles)
        self._tests = []
        # Subunit V2 stream for get_subunit_stream
        self._subunit = None

    def startTestRun(self):
        self._subunit = BytesIO()
        serialiser = subunit.v2.StreamResultToBytes(self._subunit)
        self._hook = testtools.CopyStreamResult([
            testtools.StreamToDict(self._handle_test),
            serialiser])
        self._hook.startTestRun()

    def _handle_test(self, test_dict):
        self._tests.append(test_dict)
        start, stop = test_dict['timestamps']
        if test_dict['status'] == 'exists' or None in (start, stop):
            return
        duration_delta = stop - start
        duration_seconds = ((duration_delta.microseconds +
            (duration_delta.seconds + duration_delta.days * 24 * 3600)
            * 10**6) / 10.0**6)
        self._repository._times[test_dict['id']] = duration_seconds

    def stopTestRun(self):
        self._hook.stopTestRun()
        self._repository._runs.append(self)
        self._run_id = len(self._repository._runs) - 1
        if not self._partial:
            self._repository._failing = OrderedDict()
        for test_dict in self._tests:
            test_id = test_dict['id']
            profiles = test_dict['tags'].intersection(self._profiles)
            key = (test_id, frozenset(profiles))
            if test_dict['status'] == 'fail':
                case = testtools.testresult.real.test_dict_to_case(test_dict)
                self._repository._failing[key] = case
            else:
                self._repository._failing.pop(key, None)
        return self._run_id

    def status(self, *args, **kwargs):
        self._hook.status(*args, **kwargs)

    def get_id(self):
        return self._run_id

    def get_subunit_stream(self):
        self._subunit.seek(0)
        return self._subunit

    def get_test(self):
        def wrap_result(result):
            # Wrap in a router to mask out startTestRun/stopTestRun from the
            # ExtendedToStreamDecorator.
            result = testtools.StreamResultRouter(result, do_start_stop_run=False)
            # Wrap that in ExtendedToStreamDecorator to convert v1 calls to
            # StreamResult.
            return testtools.ExtendedToStreamDecorator(result)
        return testtools.DecorateTestCaseResult(
            self, wrap_result, methodcaller('startTestRun'),
            methodcaller('stopTestRun'))

    def run(self, result):
        # Speaks original.
        for test_dict in self._tests:
            case = testtools.testresult.real.test_dict_to_case(test_dict)
            case.run(result)
