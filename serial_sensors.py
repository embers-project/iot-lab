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
import json
import sys
import iotlabcli.parser.common
from iotlabcli import experiment, get_user_credentials
from iotlabcli import helpers
from iotlabaggregator.serial import SerialAggregator
import rest
import utils
import data_handler

import HTTPError

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
group = PARSER.add_mutually_exclusive_group(required=True)
group.add_argument('--iotlab-sensors',
                   type=(lambda x: ('sensors_on %d' % _check_period(x))),
                   metavar=PERIOD_METAVAR,
                   help='iotlab sensors (temperature, pressure, light) measure period in seconds',
                   dest='iotlab_sensors')
group.add_argument('--parking',
                   type=(lambda x: ('parking_on %d' % _check_period(x))),
                   metavar=PERIOD_METAVAR,
                   help='parking event measure period in seconds (eg. Poisson distribution)',
                   dest='parking')
group.add_argument('--traffic',
                   action='store_true',
                   help='traffic event measure',
                   dest='traffic')
group.add_argument('--pollution',
                   action='store_true',
                   help='pollution event measure',
                   dest='pollution')
group.add_argument('--flash',
                   action='store_true',
                   help='flash firmware')

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
    'serial_sensors': os.path.join(FW_DIR, 'embers_sensors.elf'),
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


def _register_broker_devices(broker_api, attr_nodes):
    """
    Register experiment nodes with device broker.
    """
    broker_devices = {}
    for node, attr in attr_nodes.iteritems():
        try:
            res = broker_api.register_device(attr)
            broker_devices[node] = res
            print('Register %s device : uuid=%s token=%s' % (node, res['uuid'], res['token']))
        except HTTPError, err:
            print('Register %s device error : %s' % (node, err))
        except ConnectionError:
            print('connection error, aborting.  Devices NOT un-registered')
            sys.exit(2)
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


def _aggregate_measure(broker_api, cmd, broker_devices):
    """ Launch serial aggregator on the frontend SSH.
    """
    workers = spawn_workers(broker_api, broker_devices)
    with SerialAggregator(broker_devices.keys(),
                          line_handler=data_handler.handle_measure) as aggregator:
        # wait serial aggregator connected
        time.sleep(5)
        if cmd:
            print('Launch command : %s' % cmd)
            aggregator.broadcast(cmd+'\n')

        print('Press Ctrl+C to quit')
        super(SerialAggregator, aggregator).run()
    print('Stop handler measure')
    for worker in workers:
        worker.stop()

# pylint: disable=unused-argument
def _sighup_handler(signum, frame):
    """ catch SIGHUP signal when you kill run script
    or the experiment is stopped by the scheduler.
    It raises a keyboard exception (e.g. Ctrl-C) for
    stopping serial aggregator and unregister devices.
    """
    print('SIGHUP signal handler')
    raise KeyboardInterrupt


def _get_broker_api(opts):
    if (opts.broker_url and opts.gateway_uuid):
        broker_api = rest.MeshbluApi(opts.broker_url,
                                     opts.gateway_uuid)
    else:
        broker_api = rest.MeshbluApi.from_config('meshblu')
    return broker_api

def spawn_workers(broker_api, broker_devices):
    workers = []
    for device in broker_devices:
        w = data_handler.MeasureHandler(broker_api, broker_devices)
        w.start()
        workers.append(w)
    return workers

def _handle_traffic_data(broker_api, broker_devices, attr_nodes):
    _handle_file_data(broker_api, broker_devices, attr_nodes,
                      utils.get_traffic_data_readers,
                      utils.get_traffic_payload)

def _handle_pollution_data(broker_api, broker_devices, attr_nodes):
    _handle_file_data(broker_api, broker_devices, attr_nodes,
                      utils.get_pollution_data_readers,
                      utils.get_pollution_payload)

def _handle_file_data(broker_api, broker_devices, attr_nodes,
                      get_readers_func, get_payload_func):
    readers = get_readers_func(attr_nodes)
    workers = spawn_workers(broker_api, broker_devices)
    try:
        _do_handle_data(broker_devices.keys(), readers,
                           data_handler.handle_measure,
                           get_payload_func)
    except KeyboardInterrupt:
        print("interrupted by user, stopping...")
    for worker in workers:
        worker.stop()

def _do_handle_data(nodes, readers, line_handler, get_payload_func):
    with SerialAggregator(nodes, line_handler=line_handler) as aggregator:
        while True:
            time.sleep(60)
            for node in nodes:
                payload = get_payload_func(readers[node])
                aggregator.send_nodes([node], payload + "\n")


def main():
    """
    Main serial sensors script.
    """
    opts = PARSER.parse_args()
    user, passwd = get_user_credentials(opts.username, opts.password)
    iotlab_api = iotlabcli.Api(user, passwd)
    exp_id = _get_exp_id(iotlab_api, opts.exp_id)
    exp_nodes = _get_exp_nodes(iotlab_api, exp_id)
    if (opts.flash):
        _update_fw_exp_nodes(iotlab_api,
                             exp_id,
                             exp_nodes,
                             FW_DICT['serial_sensors'])
        return
    if (opts.iotlab_sensors):
        cmd = opts.iotlab_sensors
        node_type = 'iotlab_sensors'
    if (opts.parking):
        cmd = opts.parking
        node_type = 'parking'
    if (opts.traffic):
        cmd = None
        node_type = 'traffic'
    if (opts.pollution):
        cmd = None
        node_type = 'pollution'

    # reset nodes to be sure of init firmware execution
    _reset_exp_nodes(iotlab_api, exp_id, exp_nodes)
    broker_api = _get_broker_api(opts)
    attr_nodes = utils.get_attr_nodes(opts, node_type, exp_nodes)
    broker_devices = _register_broker_devices(broker_api, attr_nodes)

    signal.signal(signal.SIGHUP, _sighup_handler)
    if opts.traffic:
        _handle_traffic_data(broker_api, broker_devices, attr_nodes)
    elif opts.pollution:
        _handle_pollution_data(broker_api, broker_devices, attr_nodes)
    else:
        _aggregate_measure(broker_api, cmd, broker_devices)
    signal.signal(signal.SIGHUP, signal.SIG_DFL)

    _unregister_broker_devices(broker_api, broker_devices)


if __name__ == '__main__':
    main()

