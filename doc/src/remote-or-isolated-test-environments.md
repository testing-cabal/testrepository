# Remote or isolated test environments

A common problem with parallel test running is test runners that use global
resources such as well known ports, well known database names or predictable
directories on disk. 

One way to solve this is to setup isolated environments such as chroots,
containers or even separate machines. Such environments typically require
some coordination when being used to run tests, so testr provides an explicit
model for working with them.

The model testr has is intended to support both developers working
incrementally on a change and CI systems running tests in a one-off setup,
for both statically and dynamically provisioned environments.

The process testr follows is:

1. The user should perform any one-time or once-per-session setup. For instance,
   checking out source code, creating a template container, sourcing your cloud
   credentials.
2. Execute testr run.
3. testr queries for concurrency.
4. testr will make a callout request to provision that many instances.
   The provisioning callout needs to synchronise source code and do any other
   per-instance setup at this stage.
5. testr will make callouts to execute tests, supplying files that should be
   copied into the execution environment. Note that instances may be used for
   more than one command execution.
6. testr will callout to dispose of the instances after the test run completes.

Instances may be expensive to create and dispose of. testr does not perform
any caching, but the callout pattern is intended to facilitate external
caching - the provisioning callout can be used to pull environments out of
a cache, and the dispose to just return it to the cache.

## Configuring environment support

There are three callouts that testrepository depends on - configured in
.testr.conf as usual. For instance

```ini
  instance_provision=foo -c $INSTANCE_COUNT
  instance_dispose=bar $INSTANCE_IDS
  instance_execute=quux $INSTANCE_ID $FILES -- $COMMAND
```

These should operate as follows:

* instance_provision should start up the number of instances provided in the
  `$INSTANCE_COUNT` parameter. It should print out on stdout the instance ids
  that testr should supply to the dispose and execute commands. There should
  be no other output on stdout (stderr is entirely up for grabs). An exit code
  of non-zero will cause testr to consider the command to have failed. A
  provisioned instance should be able to execute the list tests command and
  execute tests commands that testr will run via the instance_execute callout.
  Its possible to lazy-provision things if you desire - testr doesn't care -
  but to reduce latency we suggest performing any rsync or other code
  synchronisation steps during the provision step, as testr may make multiple
  calls to one environment, and re-doing costly operations on each command
  execution would impair performance.

* instance_dispose should take a list of instance ids and get rid of them
  this might mean putting them back in a pool of instances, or powering them
  off, or terminating them - whatever makes sense for your project.

* instance_execute should accept an instance id, a list of files that need to 
  be copied into the instance and a command to run within the instance. It
  needs to copy those files into the instance (it may adjust their paths if
  desired). If the paths are adjusted, the same paths within `$COMMAND` should be
  adjusted to match. Execution that takes place with a shared filesystem can
  obviously skip file copying or adjusting (and the $FILES parameter). When the
  instance_execute terminates, it should use the exit code that the command
  used within the instance. Stdout and stderr from instance_execute are
  presumed to be that of `$COMMAND`. In particular, stdout is where the subunit
  test output, and subunit test listing output, are expected, and putting other
  output into stdout can lead to surprising results - such as corrupting the
  subunit stream.
  instance_execute is invoked for both test listing and test executing
  callouts.
