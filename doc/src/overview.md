# Overview

Test repository is a small application for tracking test results. Any test run
that can be represented as a subunit stream can be inserted into a repository.

Typical workflow is to have a repository into which test runs are inserted, and
then to query the repository to find out about issues that need addressing.
testr can fully automate this, but lets start with the low level facilities,
using the sample subunit stream included with testr

```sh
  # Note that there is a .testr.conf already:
  ls .testr.conf
  # Create a store to manage test results in.
  $ testr init
  # add a test result (shows failures)
  $ testr load < examples/example-failing-subunit-stream
  # see the tracked failing tests again
  $ testr failing
  # fix things
  $ testr load < examples/example-passing-subunit-stream
  # Now there are no tracked failing tests
  $ testr failing
```

Most commands in testr have comprehensive online help, and the commands

```sh
  $ testr help [command]
  $ testr commands
```

Will be useful to explore the system.
