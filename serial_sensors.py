#!/usr/bin/env python
# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB embers tools
# Copyright (C) 2015 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


"""
Serial sensors script: it flashes a firmware on experiment nodes
and runs serial aggregator library on the frontend SSH. By serial
communication we send measurement configuration to the nodes and
gather measurement data. Finally the measurement data is sending to
Meshblu broker device.
"""

from __future__ import print_function
import os
import argparse
import signal
import time
import datetime
import Queue
import threading
import json
import sys
import iotlabcli.parser.common
from iotlabcli import experiment, get_user_credentials
from iotlabcli import helpers
from iotlabaggregator.serial import SerialAggregator
import rest
# pylint: disable=import-error,no-name-in-module
# pylint: disable=wrong-import-order
try:  # pragma: no cover
    from urllib.error import HTTPError
except ImportError:  # pragma: no cover
    # pylint: disable=import-error,no-name-in-module
    from urllib2 import HTTPError

PERIOD_METAVAR = '[1-3600]'

def _check_period(data):
    value = int(data)
    if value not in xrange(1, 3601):
        raise ValueError
    return value

PARSER = argparse.ArgumentParser()
iotlabcli.parser.common.add_auth_arguments(PARSER)
PARSER.add_argument('-i',
                    '--exp-id',
                    dest='exp_id',
                    type=int,
                    help='experiment id')
PARSER.add_argument('-url',
                    '--broker-url',
                    dest='broker_url',
                    help='Meshblu device broker url')
PARSER.add_argument('-uuid',
                    '--gateway-uuid',
                    dest='gateway_uuid',
                    help='Meshblu device broker gateway')
# pylint: disable=C0103
group_sensors = PARSER.add_argument_group('sensors', 'sensors measure')
group_parking = PARSER.add_argument_group('parking', 'parking event')
group_sensors.add_argument('--sensors-period',
                           type=(lambda x: ('sensors_on %d' % _check_period(x))),
                           metavar=PERIOD_METAVAR,
                           help='measure period in seconds',
                           dest='sensors')
group_parking.add_argument('--parking-period',
                           type=(lambda x: ('parking_on %d' % _check_period(x))),
                           metavar=PERIOD_METAVAR,
                           help='parking event period in seconds (eg. Poisson distribution)',
                           dest='parking')


class MeasureHandler(threading.Thread):
    """
    Measure thread handler.
    """

    def __init__(self, broker_api, broker_devices):
        threading.Thread.__init__(self)
        # thread safe message queue
        self.queue = Queue.Queue()
        self.running = False
        self.broker_api = broker_api
        self.broker_devices = broker_devices

    def run(self):
        self.running = True
        while self.running:
            try:
                data = self.queue.get(block=True, timeout=1)
                device, payload = data.popitem()
                if device in self.broker_devices:
                    props = self.broker_devices[device]
                    res = self.broker_api.send_message(payload,
                                                       props['uuid'],
                                                       props['token'])
                    print(res)
                else:
                    print("Unknown %s device send message" % device)
            except Queue.Empty:
                pass
            except HTTPError, err:
                print('Send message %s device error : %s' % (device, err))

    def stop(self):
        """ Stop measure.
        """
        self.running = False
        self.join()

    def handle_measure(self, identifier, line):
        """ Handle measure on the serial port.
        """
        try:
            data = json.loads(line)
            now = datetime.datetime.now()
            # TODO
            # add ControlNode timestamp instead of frontend SSH
            timestamp = time.mktime(now.timetuple())
            data['timestamp'] = timestamp
        except ValueError:
            # we ignore lines not in JSON format
            return

        self.queue.put({identifier : data})


def _get_exp_id(iotlab_api, exp_id):
    """ Get experiment id """
    try:
        return helpers.get_current_experiment(iotlab_api, exp_id)
    except ValueError, err:
        print(err)
        sys.exit(1)


def _get_exp_nodes(iotlab_api, exp_id):
    """ Get experiment nodes properties """
    resources = experiment.get_experiment(iotlab_api, exp_id, 'resources')['items']
    return dict((res['network_address'], res) for res in resources)

CURRENT_DIR = os.path.relpath(os.path.dirname(__file__))
FW_DIR = os.path.join(CURRENT_DIR, 'firmwares/')
FW_DICT = {
    'serial_sensors': os.path.join(FW_DIR, 'serial_sensors.elf'),
}

def _update_fw_exp_nodes(iotlab_api, exp_id, exp_nodes, firmware_path):
    """ Update experiment nodes firmware """
    files = helpers.FilesDict()
    files.add_firmware(firmware_path)
    files['nodes.json'] = json.dumps(exp_nodes.keys())
    return iotlab_api.node_update(exp_id, files)


def _reset_exp_nodes(iotlab_api, exp_id, exp_nodes):
    """ Reset experiment nodes """
    return iotlab_api.node_command('reset', exp_id, exp_nodes.keys())


NODE_ATTR = ['network_address', 'uid', 'site', 'archi']


def _register_broker_devices(broker_api, exp_nodes):
    """
    Register experiment nodes with device broker.
    """
    broker_devices = {}
    payload = {'type': 'sensor'}
    for node, props in exp_nodes.iteritems():
        for attr in NODE_ATTR:
            payload.update({attr: props[attr]})
        try:
            res = broker_api.register_device(payload)
            broker_devices[node] = res
            print('Register %s device : uuid=%s token=%s' % (node, res['uuid'], res['token']))
        except HTTPError, err:
            print('Register %s device error : %s' % (node, err))
    return broker_devices


def _unregister_broker_devices(broker_api, broker_devices):
    """
    Unregister experiment nodes with broker device.
    """
    for device, props in broker_devices.iteritems():
        try:
            res = broker_api.unregister_device(props['uuid'],
                                               props['uuid'],
                                               props['token'])
            print('Unregister %s device : uuid=%s' % (device, res['uuid']))
        except HTTPError, err:
            print('Unregister %s device error : %s' % (device, err))


def _aggregate_measure(broker_api, cmd_list, broker_devices):
    """ Launch serial aggregator on the frontend SSH.
    """
    m_handler = MeasureHandler(broker_api, broker_devices)
    m_handler.start()
    try:
        with SerialAggregator(broker_devices.keys(),
                              line_handler=m_handler.handle_measure) as aggregator:
            # wait serial aggregator connected
            time.sleep(5)
            for cmd in cmd_list:
                print('Launch command : %s' % cmd)
                aggregator.broadcast(cmd+'\n')
            print('Press Ctrl+C to quit')
            super(SerialAggregator, aggregator).run()

    except RuntimeError as err:
        sys.stderr.write("%s\n" % err)
        exit(1)
    finally:
        print('Stop handler measure')
        m_handler.stop()

# pylint: disable=unused-argument
def _sighup_handler(signum, frame):
    """ catch SIGHUP signal when you kill run script
    or the experiment is stopped by the scheduler.
    It raises a keyboard exception (e.g. Ctrl-C) for
    stopping serial aggregator and unregister devices.
    """
    raise KeyboardInterrupt

def main():
    """
    Main serial sensors script.
    """
    cmd_list = []
    opts = PARSER.parse_args()
    if not opts.sensors and not opts.parking:
        PARSER.error("You must specify at least one period argument")
    if opts.sensors:
        cmd_list.append(opts.sensors)
    if opts.parking:
        cmd_list.append(opts.parking)
    user, passwd = get_user_credentials(opts.username, opts.password)
    iotlab_api = iotlabcli.Api(user, passwd)
    exp_id = _get_exp_id(iotlab_api, opts.exp_id)
    exp_nodes = _get_exp_nodes(iotlab_api, exp_id)
    _update_fw_exp_nodes(iotlab_api,
                         exp_id,
                         exp_nodes,
                         FW_DICT['serial_sensors'])
    # reset nodes to be sure of init firmware execution
    _reset_exp_nodes(iotlab_api, exp_id, exp_nodes)
    if (opts.broker_url and opts.gateway_uuid):
        broker_api = rest.MeshbluApi(opts.broker_url,
                                     opts.gateway_uuid)
    else:
        broker_api = rest.MeshbluApi.from_config('meshblu')
    broker_devices = _register_broker_devices(broker_api, exp_nodes)

    signal.signal(signal.SIGHUP, _sighup_handler)
    _aggregate_measure(broker_api, cmd_list, broker_devices)
    signal.signal(signal.SIGHUP, signal.SIG_DFL)

    _unregister_broker_devices(broker_api, broker_devices)


if __name__ == '__main__':
    main()

