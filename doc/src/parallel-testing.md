# Parallel testing

If both test listing and filtering (via either `IDLIST` or `IDFILE`) are configured then testr is able to run your tests in parallel

```sh
  $ testr run --parallel
```

This will first list the tests, partition the tests into one partition per CPU
on the machine, and then invoke multiple test runners at the same time, with
each test runner getting one partition. Currently the partitioning algorithm
is simple round-robin for tests that testr has not seen run before, and
equal-time buckets for tests that testr has seen run. NB: This uses the anydbm
Python module to store the duration of each test. On some platforms (to date
only OSX) there is no bulk-update API and performance may be impacted if you
have many (10's of thousands) of tests.

To determine how many CPUs are present in the machine, testrepository will
use the multiprocessing Python module (present since 2.6). On operating systems
where this is not implemented, or if you need to control the number of workers
that are used, the --concurrency option will let you do so

```sh
  $ testr run --parallel --concurrency=2
```

A more granular interface is available too - if you insert into .testr.conf

```ini
  test_run_concurrency=foo bar
```

Then when testr needs to determine concurrency, it will run that command and
read the first line from stdout, cast that to an int, and use that as the
number of partitions to create. A count of 0 is interpreted to mean one
partition per test. For instance in .test.conf

```ini
  test_run_concurrency=echo 2
```

Would tell testr to use concurrency of 2.

When running tests in parallel, testrepository tags each test with a tag for
the worker that executed the test. The tags are of the form `worker-%d`
and are usually used to reproduce test isolation failures, where knowing
exactly what test ran on a given backend is important. The `%d` that is
substituted in is the partition number of tests from the test run - all tests
in a single run with the same `worker-N` ran in the same test runner instance.

To find out which slave a failing test ran on just look at the `tags` line in
its test error

```text
  ======================================================================
  label: testrepository.tests.ui.TestDemo.test_methodname
  tags: foo worker-0
  ----------------------------------------------------------------------
  error text
```

And then find tests with that tag

```sh
  $ testr last --subunit | subunit-filter -s --xfail --with-tag=worker-3 | subunit-ls > slave-3.list
```
