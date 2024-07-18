# Setuptools integration

testrepository provides a setuptools commands for ease of integration with
setuptools-based workflows:

* testr:
  `python setup.py testr` will run testr in parallel mode
  Options that would normally be passed to testr run can be added to the
  testr-options argument.
  `python setup.py testr --testr-options="--failing"` will append `--failing`
  to the test run.
* testr --coverage:
  `python setup.py testr --coverage` will run testr in code coverage mode. This
  assumes the installation of the python coverage module.
* `python testr --coverage --omit=ModuleThatSucks.py` will append
  --omit=ModuleThatSucks.py to the coverage report command.
