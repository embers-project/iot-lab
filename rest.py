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

""" Embers Meshblu Rest API class
"""

import sys
import requests
import utils
import csv

import HTTPError


# pylint: disable=maybe-no-member,no-member
class MeshbluApi(object):
    """ Meshblu REST API """

    status_codes = [requests.codes.ok, requests.codes.created]
    
    def __init__(self, broker_url=None, gateway_uuid=None):
        self.broker_url = broker_url
        self.gateway_uuid = gateway_uuid

    @classmethod
    def from_config(cls, config):
        cfg = utils.get_broker_config(config)
        broker_url = cfg['broker_url']
        gateway_uuid = cfg['gateway_uuid']
        return cls(broker_url, gateway_uuid)

    @staticmethod
    def get_headers(auth_uuid, auth_token):
        """ get headers that will be sent with HTTP request
        """
        return {'meshblu_auth_uuid':auth_uuid, 'meshblu_auth_token':auth_token}
    
    def get_status(self):
        """ Returns the broker status.
        """
        return self.method('status')
    
    def register_device(self, payload, auth_uuid=None, auth_token=None):
        """ Register a device. Meshblu returns an UUID device id
        and security token. You can pass any key/value pairs and
        even override Meshblu's auto-generated UUID and token
        by passing your own uuid and token in the payload.

        :param payload: key/value pair dictionnary
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        if auth_uuid is not None and auth_token is not None:
            payload = payload.update({'meshblu_auth_uuid': auth_uuid,
                                      'meshblu_auth_token': auth_token})
        
        return self.method('devices',
                           'post',
                           params=payload)
        

    def unregister_device(self, uuid, auth_uuid, auth_token):
        """ Delete a device currently registered that you have
        access to update.

        :param uuid : device uuid
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('devices/' + uuid,
                           'delete',
                           headers=headers)

    def get_device(self, uuid, auth_uuid, auth_token):
        """ Returns all information (except the token) of a
        specific device or node
        
        :param uuid : device uuid
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('devices/' + uuid,
                           headers=headers)
    
    def get_devices(self, payload, auth_uuid, auth_token):
        """ Returns an array of devices based on key/value
        query criteria (except the token)

        :param payload: key/value pair dictionnary
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('devices',
                           params=payload,
                           headers=headers)

    def update_device(self, uuid, payload, auth_uuid, auth_token):
        """ Update a device currently registered.
        You can pass any key/value pairs to update object as well as
        null to remove a propery (i.e. uid=null).

        :param uuid : device uuid
        :param payload: key/value pair dictionnary
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('devices/' + uuid,
                           'put',
                           params=payload,
                           headers=headers)

    def claim_device(self, uuid, auth_uuid, auth_token):
        """ claim ownership of another device
        
        :param uuid : device uuid
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('claimdevice/' + uuid,
                           'put',
                           headers=headers)
        
    
    def subscribe_device(self, auth_uuid, auth_token):
        """ Subscribe to device
        
        :param uuid : device uuid
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        return self.method('subscribe/' + uuid,
                           headers=headers)
        
    
    def send_message(self, payload, auth_uuid, auth_token):
        """Send a message to devices

        :param devices: gateway devices ("uuid", "*", ["uuid1", "uuid2"])
        :param payload:  key/value pair dictionnary
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        message = {"devices": self.gateway_uuid,
                   "payload": payload}
        return self.method('messages', 'post',
                           json=message,
                           headers=headers)


    def send_data(self, uuid, payload, auth_uuid, auth_token):
        """Store sensor data for a device

        :param uuid : device uuid
        :param payload:  key/value pair dictionnary
        :param auth_uuid: uuid authentication credential
        :param auth_token: secret token authentication credential
        """
        headers = self.get_headers(auth_uuid, auth_token)
        self.method('data/' + uuid, 'post', params=payload, headers=headers)


    def method(self, url, method='get',  # pylint:disable=too-many-arguments
               json=None, params=None, headers=None, raw=False):
        """
        Call http `method`

        :param url: url of API.
        :param method: request method
        :param json: send as 'post' json encoded data
        :param params : dictionary sent in the query string
        :param headers : dictionary of HTTP headers
        :param raw: Should data be loaded as json or not
        """
        assert method in ('get', 'post', 'delete', 'put')
        _url = self.broker_url + "/" + url

        req = requests.request(
            method,
            _url,
            json=json,
            params=params,
            headers=headers)

        if req.status_code in self.status_codes:
            return req.content if raw else req.json()

        # Indent req.text to pretty print it later
        indented_lines = ['\t' + l for l in req.text.splitlines(True)]
        msg = '\n' + ''.join(indented_lines)
        raise HTTPError(_url, req.status_code, msg, req.headers, None)

    
