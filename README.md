# Test Repository

![build status](https://badgen.net/github/checks/testing-cabal/testrepository)

## Overview

This project provides a database of test results which can be used as part of
developer workflow to ensure/check things like:

* No commits without having had a test failure, test fixed cycle.
* No commits without new tests being added.
* What tests have failed since the last commit (to run just a subset).
* What tests are currently failing and need work.

Test results are inserted using subunit (and thus anything that can output
subunit or be converted into a subunit stream can be accepted).

A mailing list for discussion, usage and development is at
https://launchpad.net/~testrepository-dev - all are welcome to join. Some folk
hang out on #testrepository on irc.freenode.net.

CI for the project is GitHub Actions at https://github.com/testing-cabal/testrepository.

## Licensing

Test Repository is under BSD / Apache 2.0 licences. See the file COPYING in the source for details.

## Quick Start

Create a config file::

```sh
  $ touch .testr.conf
```

Create a repository::

```sh
  $ testr init
```

Load a test run into the repository::

```sh
  $ testr load < testrun
```

Query the repository::

```sh
  $ testr stats
  $ testr last
  $ testr failing
```

Delete a repository::

```sh
  $ rm -rf .testrepository
```

## Documentation

More detailed documentation including design and implementation details, a
user manual, and guidelines for development of Test Repository itself can be
found at https://testing-cabal.github.io/testrepository/, or in the source
tree at doc/ (run make -C doc html).
