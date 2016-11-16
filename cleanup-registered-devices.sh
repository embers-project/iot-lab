#!/bin/bash

echo "Please copy/paste the 'Register' lines of the ./serial_sensors.py log"
echo "and hit ^D when done.  You may paste several log lines at once."
echo

grep Register | awk -F '=| ' '{
	uuid  = $6
	token = $8
	system("curl -X DELETE http://msg2.embers.citibrain.com/devices/" uuid \
		" --header meshblu_auth_uuid:" uuid " --header meshblu_auth_token:" token )
	print ""
}'
