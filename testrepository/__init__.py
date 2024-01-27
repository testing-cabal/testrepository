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

"""The testrepository library.

This library is divided into some broad areas.

The commands package contains the main user entry points into the application.
The ui package contains various user interfaces.
The repository package contains the core storage code.
The tests package contains tests and test specific support code.
"""

# Yes, this is not PEP-396 compliant. It predates that.
from pbr.version import VersionInfo

_v = VersionInfo('testrepository').semantic_version()
version = _v.release_string()
__version__ = _v.version_tuple()
