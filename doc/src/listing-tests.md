# Listing Tests

It is useful to be able to query the test program to see what tests will be
run - this permits partitioning the tests and running multiple instances with
separate partitions at once. Set 'test_list_option' in .testr.conf like so:

```ini
  test_list_option=--list-tests
```

You also need to use the $LISTOPT option to tell testr where to expand things:

```ini
  test_command=foo $LISTOPT $IDOPTION
```

All the normal rules for invoking test program commands apply: extra parameters
will be passed through, if a test list is being supplied test_option can be
used via `$IDOPTION`.

The output of the test command when this option is supplied should be a subunit
test enumeration. For subunit v1 that is a series of test ids, in any order,
``\n`` separated on stdout. For v2 use the subunit protocol and emit one event
per test with each test having status 'exists'.

To test whether this is working the `testr list-tests` command can be useful.

You can also use this to see what tests will be run by a given testr run
command. For instance, the tests that `testr run myfilter` will run are shown
by `testr list-tests myfilter`. As with `run`, arguments to `list-tests` are
used to regex filter the tests of the test runner, and arguments after a `--`
are passed to the test runner.
