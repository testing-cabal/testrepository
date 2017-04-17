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

"""Storage of test results.

A Repository provides storage and indexing of results.

The AbstractRepository class defines the contract to which any Repository 
implementation must adhere.

The file submodule is the usual repository that code will use for local
access, and the memory submodule provides a memory only repository useful for
testing.

Repositories are identified by their URL, and new ones are made by calling
the initialize function in the appropriate repository module.

Repositories may have very different implementations - web services,
databases, in-memory stores. Their guaranteed behaviour is defined by the
contract tests in the test suite (tests.test_repository).
"""

import warnings

from testtools import StreamToDict, TestResult


class AbstractRepositoryFactory(object):
    """Interface for making or opening repositories."""

    def initialise(self, url):
        """Create a repository at URL. 

        Call on the class of the repository you wish to create.
        """
        raise NotImplementedError(self.initialise)

    def open(self, url):
        """Open the repository at url.

        Raise RepositoryNotFound if there is no repository at the given url.
        """
        raise NotImplementedError(self.open)


class AbstractRepository(object):
    """The base class for Repository implementations.

    There are no interesting attributes or methods as yet.
    """

    def count(self):
        """Return the number of test runs this repository has stored.
        
        :return count: The count of test runs stored in the repositor.
        """
        raise NotImplementedError(self.count)

    def get_failing(self):
        """Get a TestRun that contains all of and only current failing tests.

        :return: a TestRun.
        """
        raise NotImplementedError(self.get_failing)

    def get_inserter(self, partial=False, profiles=None):
        """Get an inserter that will insert a test run into the repository.

        Repository implementations should implement _get_inserter.

        get_inserter() does not add timing data to streams: it should be
        provided by the caller of get_inserter (e.g. commands.load).

        :param partial: If True, the stream being inserted only executed some
            tests rather than all the projects tests.
        :param profiles: An iterable of the profiles that may be in use. This
            can be used by repositories that implement materialized lists of
            failing tests to eliminate non-profile tags (e.g. those that do
            not represent a distinct test instance).
        :return an inserter: Inserters meet the StreamResult protocol
            that testtools 1.0.0 and above offer. The startTestRun and
            stopTestRun methods in particular must be called.
        """
        try:
            if profiles is None:
                profiles = set()
            return self._get_inserter(partial, profiles)
        except TypeError:
            warnings.warn(
                "Repository._get_inserter missing profiles support.",
                DeprecationWarning)
            return self._get_inserter(partial)
    
    def _get_inserter(self, partial, profiles):
        """Get an inserter for get_inserter.
        
        The result is decorated with an AutoTimingTestResultDecorator.

        :param partial: If True, the stream being inserted only executed some
            tests rather than all the projects tests.
        :param profiles: An iterable of the profiles that may be in use. This
            can be used by repositories that implement materialized lists of
            failing tests to eliminate non-profile tags (e.g. those that do
            not represent a distinct test instance).
        """
        raise NotImplementedError(self._get_inserter)

    def get_latest_run(self):
        """Return the latest run.

        Equivalent to get_test_run(latest_id()).
        """
        return self.get_test_run(self.latest_id())

    def get_test_run(self, run_id):
        """Retrieve a TestRun object for run_id.

        :param run_id: The test run id to retrieve.
        :return: A TestRun object.
        """
        raise NotImplementedError(self.get_test_run)

    def get_test_times(self, test_ids):
        """Retrieve estimated times for the tests test_ids.

        :param test_ids: The test ids to query for timing data.
        :return: A dict with two keys: 'known' and 'unknown'. The unknown
            key contains a set with the test ids that did run. The known
            key contains a dict mapping test ids to time in seconds.
        """
        test_ids = frozenset(test_ids)
        known_times = self._get_test_times(test_ids)
        unknown_times = test_ids - set(known_times)
        return dict(known=known_times, unknown=unknown_times)

    def _get_test_times(self, test_ids):
        """Retrieve estimated times for tests test_ids.

        :param test_ids: The test ids to query for timing data.
        :return: A dict mapping test ids to duration in seconds. Tests that no
            timing data is present for should not be returned - the base class
            get_test_times function will collate the missing test ids and put
            that in to its result automatically.
        """
        raise NotImplementedError(self._get_test_times)

    def latest_id(self):
        """Return the run id for the most recently inserted test run."""
        raise NotImplementedError(self.latest_id)

    def get_test_ids(self, run_id):
        """Return the test ids from the specified run.

        :param run_id: the id of the test run to query.
        :return: a list of test ids for the tests that
            were part of the specified test run.
        """
        run = self.get_test_run(run_id)
        ids = []
        def gather(test_dict):
            ids.append(test_dict['id'])
        result = StreamToDict(gather)
        result.startTestRun()
        try:
            run.get_test().run(result)
        finally:
            result.stopTestRun()
        return ids


class AbstractTestRun(object):
    """A test run that has been stored in a repository.
    
    Should implement the StreamResult protocol as well
    as the testrepository specific methods documented here.
    """

    def get_id(self):
        """Get the id of the test run.

        Sometimes test runs will not have an id, e.g. test runs for
        'failing'. In that case, this should return None.
        """
        raise NotImplementedError(self.get_id)

    def get_subunit_stream(self):
        """Get a subunit stream for this test run."""
        raise NotImplementedError(self.get_subunit_stream)

    def get_test(self):
        """Get a testtools.TestCase-like object that can be run.

        :return: A TestCase like object which can be run to get the individual
            tests reported to a testtools.StreamResult/TestResult.
            (Clients of repository should provide an ExtendedToStreamDecorator
            decorator to permit either API to be used).
        """
        raise NotImplementedError(self.get_test)


class RepositoryNotFound(Exception):
    """Raised when we try to open a repository that isn't there."""

    def __init__(self, url):
        self.url = url
        msg = 'No repository found in %s. Create one by running "testr init".'
        Exception.__init__(self, msg % url)
