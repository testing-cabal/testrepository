# Repositories

A testr repository is a very simple disk structure. It contains the following
files (for a format 1 repository - the only current format):

* `format`: This file identifies the precise layout of the repository, in case future changes are needed.

* `next-stream`: This file contains the serial number to be used when adding another stream to the repository.

* `failing`: This file is a stream containing just the known failing tests.
  It is updated whenever a new stream is added to the repository, so that it only references known failing tests.

* `#N` - all the streams inserted in the repository are given a serial number.

* `repo.conf`: This file contains user configuration settings for the repository.
  `testr repo-config` will dump a repo configration and `test help repo-config` has online help for all the repository settings.
