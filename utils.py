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
import json
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


        
