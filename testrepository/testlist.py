#
# Copyright (c) 2012 Testrepository Contributors
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

"""Handling of lists of tests - common code to --load-list etc."""

from io import BytesIO

from subunit import ByteStreamToStreamResult
from testtools.testresult.doubles import StreamResult


def write_list(stream, test_ids):
    """Write test_ids out to stream.

    :param stream: A file-like object.
    :param test_ids: An iterable of test ids.
    """
    stream.write(("\n".join(list(test_ids) + [""])).encode("utf8"))


def parse_list(list_bytes):
    """Parse list_bytes into a list of test ids."""
    return [id.strip() for id in list_bytes.decode("utf8").split("\n") if id.strip()]


def parse_enumeration(enumeration_bytes):
    """Parse enumeration_bytes into a list of test_ids."""
    parser = ByteStreamToStreamResult(
        BytesIO(enumeration_bytes), non_subunit_name="stdout"
    )
    result = StreamResult()
    parser.run(result)
    return [event[1] for event in result._events if event[2] == "exists"]
