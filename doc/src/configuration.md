# Configuration

testr is configured via the `.testr.conf` file which needs to be in the same
directory that testr is run from. testr includes online help for all the
options that can be set within it:

```sh
  $ testr help run
```

## Python

If your test suite is written in Python, the simplest - and usually correct
configuration is:

```ini
    [DEFAULT]
    test_command=python -m subunit.run discover . $LISTOPT $IDOPTION
    test_id_option=--load-list $IDFILE
    test_list_option=--list
```
