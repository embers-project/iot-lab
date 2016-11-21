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

"""Utils methods"""

import sys
import csv
from ConfigParser import SafeConfigParser, ParsingError

CONFIG_FILE = 'broker.cfg'

def get_broker_config(broker_name):
    try:
        parser = SafeConfigParser()
        with open(CONFIG_FILE) as conf_f:
            parser.readfp(conf_f)
            if parser.has_section(broker_name):
                config = dict(parser.items(broker_name))
                if any(option == '' for option in config.itervalues()):
                    raise ParsingError('%s %s config is empty' % (CONFIG_FILE,
                                                                  broker_name))
                return config
            else:
                raise ParsingError('%s %s config doesn\'t exist' % (CONFIG_FILE,
                                                                    broker_name))
    except IOError:
        print 'Config file %s doesn\'t exist' % CONFIG_FILE
        sys.exit(1)
    except ParsingError, err:
        print err
        sys.exit(1)

REGISTRY_FILE = 'registry-devices.csv'

def get_registry_device(node):
    try:
        with open(REGISTRY_FILE, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['device'] == node:
                    return {'uuid': row['uuid'], 'token': row['token']}
    except IOError:
        pass
    return None

def store_registry_device(node, uuid, token):
    with open(REGISTRY_FILE, 'a') as csvfile:
        fieldnames = ['device', 'uuid', 'token']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:
            writer.writeheader()
        writer.writerow({'device': node, 'uuid': uuid, 'token': token})


def remove_registry_device(node):
    from cStringIO import StringIO
    tmp_devices = StringIO()

    with open(REGISTRY_FILE, 'r') as csvfile:
        reader = csv.reader(csvfile)
        writer = csv.writer(tmp_devices)
        for row in reader:
            if row[0] != node:
               writer.writerow(row)

    with open(REGISTRY_FILE, 'w') as csvfile:
        csvfile.write(tmp_devices.getvalue())


NODE_ATTR = ['network_address', 'uid', 'site', 'archi']

def get_iotlab_attrs(exp_nodes):
    attr_nodes = {}
    for node, props in exp_nodes.iteritems():
        attrs = {}
        for attr in NODE_ATTR:
            attrs.update({attr: props[attr]})
        attr_nodes[node] = attrs
    return attr_nodes

def get_iotlab_parking_coordinates(site):
    iotlab_parking_coordinates = {}
    with open('coordinates/parking/%s.csv' % site) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            node = '%s.%s.iot-lab.info' % (row['node'], site)
            iotlab_parking_coordinates[node] = \
                {'longitude': row['longitude'], 'latitude': row['latitude']}
    return iotlab_parking_coordinates

def get_parking_coordinates(exp_nodes):
    iotlab_parking_coordinates = {}
    parking_coordinates = {}
    for node, attr in exp_nodes.iteritems():
        if node not in iotlab_parking_coordinates:
            iotlab_parking_coordinates.update(get_iotlab_parking_coordinates(attr['site']))
        # static allocation only for a subset of iotlab nodes site
        if node in iotlab_parking_coordinates:
            parking_coordinates[node] = iotlab_parking_coordinates[node]
    return parking_coordinates

def get_traffic_metadata(exp_nodes):
    traffic_metadata = {}
    with open('datasets/citypulse/traffic_metadata.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for node, attr in exp_nodes.iteritems():
            metadata = reader.next()
            for discard in [ 'REPORT_NAME', 'RBA_ID', '_id' ]:
                del metadata[discard]
            traffic_metadata[node] = metadata

    return traffic_metadata

def get_traffic_data_readers(attr_nodes):
    data_readers = {}
    datafile_path = 'datasets/citypulse/traffic_feb_june/trafficData%s.csv'
    for node, attr in attr_nodes.iteritems():
        csvfile = open(datafile_path % attr['REPORT_ID'])
        data_readers[node] = csv.DictReader(csvfile)
    return data_readers

def get_traffic_payload(reader):
    vehicle_count = reader.next()['vehicleCount']
    payload = "traffic %s" % vehicle_count
    return payload

def get_attr_nodes(opts, node_type, exp_nodes):
    if opts.traffic or opts.pollution:
        metadata = get_traffic_metadata(exp_nodes)
    else:
        metadata = get_parking_coordinates(exp_nodes)

    iotlab_attrs = get_iotlab_attrs(exp_nodes)

    attr_nodes = {}
    for node in exp_nodes:
        attr_nodes[node] = {'type': node_type}
    for node in iotlab_attrs:
        attr_nodes[node].update(iotlab_attrs[node])
    for node in metadata:
        attr_nodes[node].update(metadata[node])

    return attr_nodes

def get_pollution_data_readers(attr_nodes):
    data_readers = {}
    datafile_path = 'datasets/citypulse/pollution/pollutionData%s.csv'
    for node, attr in attr_nodes.iteritems():
        csvfile = open(datafile_path % attr['REPORT_ID'])
        data_readers[node] = csv.DictReader(csvfile)
    return data_readers

def get_pollution_payload(reader):
    fields = [
        "ozone", "particullate_matter", "carbon_monoxide",
        "sulfure_dioxide", "nitrogen_dioxide",
        # longitude,latitude,timestamp
    ]
    data = reader.next()
    payload = "pollution %s" % ",".join([data[f] for f in fields])
    return payload
