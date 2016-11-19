#!/usr/bin/env python

import rest
import utils
import json

def main():
    config = 'meshblu' # section = [meshblu]
    cfg = utils.get_broker_config(config)
    api = rest.MeshbluApi.from_config(config)

    uuid, token = (cfg['gateway_uuid'], cfg['gateway_token'])
    x = api.get_devices(None, uuid, token) 

    print(json.dumps(x))

main()
