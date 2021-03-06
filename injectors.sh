#!/bin/bash

usage() {
	echo "$PROG [setup|deploy|run|kill|stop]"
}

DURATION=120


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
	echo
	echo "parking_uuid   = 08769d4a-7bd9-4a2d-9b2a-b5e0ae292551"
	echo "traffic_uuid   = 5391cdbf-8920-4980-bf80-3e920e080b65"
	echo "pollution_uuid = 327f8603-5547-46f1-ab71-2804fdb61b6b"
	) > broker.cfg
}

deploy() {
	e1=`submit_experiment set2`
	e2=`submit_experiment set3`
	e3=`submit_experiment set4`
	for id in $e1 $e2 $e3 ; do
		experiment-cli wait -i $id
		./serial_sensors.py -i $id --flash
	done
}

run() {
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
	nodes_set=$1
	experiment-cli submit \
			-d $DURATION \
			-l $HOSTNAME,m3,`echo $(<$nodes_set) | tr ' ' +` \
	| awk '/id/ {print $2}'
}

get_running_experiments() {
	experiment-cli get -l --state Running \
	| awk -F '[:,]' '/"id"/ { print $2 }'
}

PROG=`basename "$0"`

cd "`dirname "$0"`"

main "$@"
