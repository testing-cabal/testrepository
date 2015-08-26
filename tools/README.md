Example scripts for doing environments/parallel with containers. Use at own
risk. We'll get something properly supportable and so on together (unless
someone else writes it!) at some point.

Needs a locally edited .testr.conf
```
--- a/.testr.conf
+++ b/.testr.conf
@@ -3,3 +3,7 @@ test_command=${PYTHON:-python} -m subunit.run discover $LISTOPT $IDOPTION
 test_id_option=--load-list $IDFILE
 test_list_option=--list
 ;filter_tags=worker-0
+list_profiles=echo 2.6 2.7 3.2 3.3 3.4 3.5 cpython pypy pypy3
+instance_provision=tools/start-container $PROFILE $INSTANCE_COUNT
+;instance_dispose=
+instance_execute=tools/run-container $PROFILE $INSTANCE_ID $FILES -- $COMMAND
```
