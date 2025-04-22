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

"""Get help on a command."""

import testrepository
from testrepository.arguments import command
from testrepository.commands import (
    Command,
    get_command_parser,
)


class help(Command):
    """Get help on a command."""

    args = [command.CommandArgument("command_name", min=0)]

    def run(self):
        if not self.ui.arguments["command_name"]:
            version = ".".join(map(str, testrepository.__version__))
            help = (
                """testr %s -- a free test repository
https://launchpad.net/testrepository/

testr commands -- list commands
testr quickstart -- starter documentation
testr help [command] -- help system
"""
                % version
            )
        else:
            cmd = self.ui.arguments["command_name"][0]
            parser = get_command_parser(cmd)
            help = parser.format_help()
        self.ui.output_rest(help)
        return 0
