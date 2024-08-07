# Development guidelines

## Coding style

PEP-8 please. We don't enforce a particular style, but being reasonably 
consistent aids readability.

## Copyrights and licensing

Code committed to Test Repository must be licensed under the BSD + Apache-2.0
licences that Test Repository offers its users. Copyright assignment is not
required. Please see COPYING for details about how to make a license grant in
a given source file. Lastly, all copyright holders need to add their name
to the master list in COPYING the first time they make a change in a given
calendar year.

## Testing and QA

For Test repository please add tests where possible. There is no requirement
for one test per change (because somethings are much harder to automatically
test than the benfit from such tests). Fast tests are preferred to slow tests,
and understandable tests to fast tests.

CI is done via Github Actions. A broken trunk is not acceptable!

See DESIGN.txt for information about code layout which will help you find
where to add tests (and indeed where to change things).

### Running the tests

Generally just ``make`` is all that is needed to run all the tests. However
if dropping into pdb, it is currently more convenient to use
``python -m testtools.run testrepository.tests.test_suite``.

### Diagnosing issues

The cli UI will drop into pdb when an error is thrown if TESTR_PDB is set in
the environment. This can be very useful for diagnosing problems.

### Releasing

Update NEWS and testrepository/__init__.py version numbers. Release to pypi.
Pivot the next milestone on LP to version, and make a new next milestone.
Make a new tag and push that to github.
