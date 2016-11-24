#!/bin/bash

usage() {
	echo "$PROG [setup|deploy|run|kill|stop]"
}

DURATION=120
#NB_SENSORS=50
NB_SENSORS=2


main() {
	case $1 in
		setup|deploy|run|kill|stop)
			$1
			;;
		-h|--help|"")
			usage
			;;
		*)
			echo "$PROG: invalid command '$1'"
			exit 1
			;;
	esac
}

setup() {
	(cd datasets/citypulse
	tar xf traffic_feb_jun_2014.tar.bz2
	tar xf pollution_aug_oct_2014.tar.bz2
	)
	(
	echo "[meshblu]"
	echo "broker_url = http://msg.embers.city"
	echo "gateway_uuid = 0d4815f-b0e8-450c-b308-db090ddc68fb"
	) > broker.cfg
}

deploy() {
	e1=`submit_experiment`
	e2=`submit_experiment`
	e3=`submit_experiment`
	for id in $e1 $e2 $e3 ; do
		experiment-cli wait -i $id
		./serial_sensors.py -i $id --flash
	done
}

run() {
	#exp_ids=`get_running_experiments`
	exp_ids=`get_running_experiments`
	i=0
	for id in $exp_ids; do
		i=$[i+1] ; eval "e$i=$id";
	done
	./serial_sensors.py -i $e1 --parking 300 &> parking.log   </dev/null &
	./serial_sensors.py -i $e2 --traffic     &> traffic.log   </dev/null &
	./serial_sensors.py -i $e3 --pollution   &> pollution.log </dev/null &
}

kill() {
	injectors=`ps x | grep -v grep | grep ./serial_sensors.py | awk '{print $1}'`
	for pid in $injectors ; do
		/bin/kill -HUP $pid
	done
}

stop() {
	exp_ids=`get_running_experiments`
	for id in $exp_ids; do
		experiment-cli stop -i $id
	done
}

submit_experiment() {
	experiment-cli submit \
			-d $DURATION \
			-l $NB_SENSORS,archi=m3:at86rf231+site=$HOSTNAME \
	| awk '/id/ {print $2}'
}

get_running_experiments() {
	experiment-cli get -l --state Running \
	| awk -F '[:,]' '/"id"/ { print $2 }'
}

PROG=`basename "$0"`

cd "`dirname "$0"`"

main "$@"
