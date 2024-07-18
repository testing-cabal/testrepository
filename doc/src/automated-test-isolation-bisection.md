# Automated test isolation bisection

As mentioned previously, it is possible to manually analyze test isolation
issues by interrogating the repository for which tests ran on which worker, and
then creating a list file with those tests, re-running only half of them,
checking the error still happens, rinse and repeat.

However that is tedious. testr can perform this analysis for you

```sh
  $ testr run --analyze-isolation 
```

will perform that analysis for you. (This requires that your test runner is
(mostly) deterministic on test ordering). The process is:

1. The last run in the repository is used as a basis for analysing against -
   tests are only cross checked against tests run in the same worker in that
   run. This means that failures accrued from several different runs would not
   be processed with the right basis tests - you should do a full test run to
   seed your repository. This can be local, or just testr load a full run from
   your Jenkins or other remote run environment.

2. Each test that is currently listed as a failure is run in a test process
   given just that id to run.

3. Tests that fail are excluded from analysis - they are broken on their own.

4. The remaining failures are then individually analysed one by one.

5. For each failing, it gets run in one work along with the first 1/2 of the
   tests that were previously run prior to it.

6. If the test now passes, that set of prior tests are discarded, and the
   other half of the tests is promoted to be the full list. If the test fails
   then other other half of the tests are discarded and the current set
   promoted.

7. Go back to running the failing test along with 1/2 of the current list of
   priors unless the list only has 1 test in it. If the failing test still
   failed with that test, we have found the isolation issue. If it did not
   then either the isolation issue is racy, or it is a 3-or-more test
   isolation issue. Neither of those cases are automated today.

This cannot prove the absence of interactions - for instance, a runner that randomises the order of tests executing combined with a failure that occurs with A before B but not B before A could easily appear to be isolated when it is not.
