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

all: README.rst check

editable:
	pip install -e .[test]

.testrepository:
	./testr init

check: editable .testrepository
	# Run without containers/multiple profiles by default.
	./testr run --parallel -p DEFAULT

check-xml:
	python -m subunit.run testrepository.tests.test_suite | subunit2junitxml -o test.xml -f | subunit2pyunit

release:
	./setup.py sdist upload --sign

README.rst: editable testrepository/commands/quickstart.py
	./testr quickstart > $@

${venv}/testr-installed-stamp: requirements.txt setup.cfg
	${venv}/bin/pip -q install -e .[test]
	touch ${venv}/testr-installed-stamp


install-for-test: ${venv}/testr-installed-stamp
	@#  nothing

.PHONY: check check-xml editable install-for-test release all
