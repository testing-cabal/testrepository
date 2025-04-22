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

"""Show the current failures in the repository."""

import optparse

import testtools

from testrepository.commands import Command
from testrepository.testcommand import TestCommand


class failing(Command):
    """Show the current failures known by the repository.

    Today this is the failures from the most recent run, but once partial
    and full runs are understood it will be all the failures from the last
    full run combined with any failures in subsequent partial runs, minus any
    passes that have occured in a run more recent than a given failure. Deleted
    tests will only be detected on full runs with this approach.

    Without --subunit, the process exit code will be non-zero if the test run
    was not successful. With --subunit, the process exit code is non-zero if
    the subunit stream could not be generated successfully.
    """

    options = [
        optparse.Option(
            "--subunit",
            action="store_true",
            default=False,
            help="Show output as a subunit stream.",
        ),
        optparse.Option(
            "--list",
            action="store_true",
            default=False,
            help="Show only a list of failing tests.",
        ),
    ]
    # Can be assigned to to inject a custom command factory.
    command_factory = TestCommand

    def _show_subunit(self, run):
        stream = run.get_subunit_stream()
        self.ui.output_stream(stream)
        return 0

    def _make_result(self, repo):
        testcommand = self.command_factory(self.ui, repo)
        if self.ui.options.list:
            list_result = testtools.StreamSummary()
            return list_result, list_result
        else:
            return self.ui.make_result(repo.latest_id, testcommand)

    def run(self):
        repo = self.repository_factory.open(self.ui.here)
        run = repo.get_failing()
        if self.ui.options.subunit:
            return self._show_subunit(run)
        case = run.get_test()
        failed = False
        result, summary = self._make_result(repo)
        result.startTestRun()
        try:
            case.run(result)
        finally:
            result.stopTestRun()
        failed = not summary.wasSuccessful()
        if failed:
            result = 1
        else:
            result = 0
        if self.ui.options.list:
            failing_tests = [test for test, _ in summary.errors + summary.failures]
            self.ui.output_tests(failing_tests)
        return result
