#
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 Testrepository Contributors
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

"""setuptools/distutils commands to run testr via setup.py

Currently provides 'testr' which runs tests using testr. You can pass
--coverage which will also export PYTHON='coverage run --source <your package>'
and automatically combine the coverage from each testr backend test runner
after the run completes.

To use, just use setuptools/distribute and depend on testr, and it should be
picked up automatically (as the commands are exported in the testrepository
package metadata.
"""

from distutils import cmd
import distutils.errors
import logging
import os
import sys

from testrepository import commands
from testrepository.repository.file import get_base

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
logger.info("imported")


class Testr(cmd.Command):

    description = "Run unit tests using testr"

    user_options = [
        ('coverage', None, "Replace PYTHON with coverage and merge coverage "
         "from each testr worker."),
        ('testr-args=', 't', "Run 'testr' with these args"),
        ('omit=', 'o', 'Files to omit from coverage calculations'),
        ('coverage-package-name=', None, "Use this name for coverage package"),
        ('slowest', None, "Show slowest test times after tests complete."),
    ]

    boolean_options = ['coverage', 'slowest']

    def _run_testr(self, *args):
        logger.info("_run_testr called")
        return commands.run_argv([sys.argv[0]] + list(args),
                                 sys.stdin, sys.stdout, sys.stderr)

    def initialize_options(self):
        logger.info("initialize_options called")
        self.testr_args = None
        self.coverage = None
        self.omit = ""
        self.slowest = None
        self.coverage_package_name = None

    def finalize_options(self):
        logger.info("finalize_options called")
        if self.testr_args is None:
            self.testr_args = []
        else:
            self.testr_args = self.testr_args.split()
        if self.omit:
            self.omit = "--omit=%s" % self.omit

    def run(self):
        """Set up testr repo, then run testr"""
        logger.info("run called")
        if not os.path.isdir(get_base()):
            self._run_testr("init")

        if self.coverage:
            self._coverage_before()
        testr_ret = self._run_testr("run", "--parallel", *self.testr_args)
        if testr_ret:
            raise distutils.errors.DistutilsError(
                "testr failed (%d)" % testr_ret)
        if self.slowest:
            print ("Slowest Tests")
            self._run_testr("slowest")
        if self.coverage:
            self._coverage_after()

    def _coverage_before(self):
        logger.info("_coverage_before called")
        package = self.distribution.get_name()
        if package.startswith('python-'):
            package = package[7:]

        # Use this as coverage package name
        if self.coverage_package_name:
            package = self.coverage_package_name
        options = "--source %s --parallel-mode" % package
        os.environ['PYTHON'] = ("coverage run %s" % options)
        logger.info("os.environ['PYTHON'] = %r", os.environ['PYTHON'])

    def _coverage_after(self):
        logger.info("_coverage_after called")
        os.system("coverage combine")
        os.system("coverage html -d ./cover %s" % self.omit)
