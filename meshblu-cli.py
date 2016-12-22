#!/usr/bin/env python

import rest
import utils
import json
import sys

def main():
    if len(sys.argv) < 2:
        print("usage: " + sys.argv[0] +
		" [list|register|unregister <uuid> <token>])")
        return
    cmd = sys.argv[1]
    if   cmd == "list":
        list_devices()
    elif cmd == "register":
        register_device()
    elif cmd == "unregister":
        unregister_device({ "uuid": sys.argv[2], "token": sys.argv[3] })
    else:
        print("unknown command: " + cmd)
        sys.exit(1)

def get_meshblu_api():
    config = 'meshblu' # section = [meshblu]
    cfg = utils.get_broker_config(config)
    api = rest.MeshbluApi.from_config(config)

    api.gw_uuid = cfg['gateway_uuid']
    api.gw_token = cfg['gateway_token']
    return api

def list_devices():
    api = get_meshblu_api()
    x = api.get_devices(None, api.gw_uuid, api.gw_token)
    print(json.dumps(x))

def register_device():
    api = get_meshblu_api()
    register_payload = { "test_device": "ofa" }
    device = api.register_device(register_payload)
    print(json.dumps(device))

def unregister_device(device):
    api = get_meshblu_api()
    ret = api.unregister_device(device["uuid"], device["uuid"], device["token"])
    print(json.dumps(ret))

main()
