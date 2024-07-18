# Hiding tests

Some test runners (for instance, `zope.testrunner`) report pseudo tests having to
do with bringing up the test environment rather than being actual tests that
can be executed. These are only relevant to a test run when they fail - the
rest of the time they tend to be confusing. For instance, the same 'test' may
show up on multiple parallel test runs, which will inflate the 'executed tests'
count depending on the number of worker threads that were used. Scheduling such
'tests' to run is also a bit pointless, as they are only ever executed
implicitly when preparing (or finishing with) a test environment to run other
tests in.

testr can ignore such tests if they are tagged, using the filter_tags
configuration option. Tests tagged with any tag in that (space separated) list
will only be included in counts and reports if the test failed (or errored).
