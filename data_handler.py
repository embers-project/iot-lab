from __future__ import print_function
import threading
import Queue
import json
import datetime
import time

# pylint: disable=import-error,no-name-in-module
# pylint: disable=wrong-import-order
try:  # pragma: no cover
    from urllib.error import HTTPError
except ImportError:  # pragma: no cover
    # pylint: disable=import-error,no-name-in-module
    from urllib2 import HTTPError


class MeasureHandler(threading.Thread):
    """
    Measure thread handler.
    """

    def __init__(self, broker_api, broker_devices):
        threading.Thread.__init__(self)
        # thread safe message queue
        self.running = False
        self.broker_api = broker_api
        self.broker_devices = broker_devices

    def run(self):
        self.running = True
        while self.running:
            try:
                data = _queue.get(block=True, timeout=1)
                device, payload = data.popitem()
                if device in self.broker_devices:
                    props = self.broker_devices[device]
                    res = self.broker_api.send_message(payload,
                                                       props['uuid'],
                                                       props['token'])
                    print(time.strftime("%F %T"), device, res)
                else:
                    print("Unknown %s device send message" % device)
            except Queue.Empty:
                pass
            except HTTPError, err:
                print('Send message %s device error : %s' % (device, err))
            except ConnectionError:
                print('Send message connection error (device: %s)' % device)

    def stop(self):
        """ Stop measure.
        """
        self.running = False
        self.join()


_queue = Queue.Queue()

def handle_measure(identifier, line):
        """ Handle measure on the serial port.
        """
        try:
            data = json.loads(line)
            now = datetime.datetime.utcnow()
            # TODO
            # add ControlNode timestamp instead of frontend SSH
            data['gateway_timestamp'] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            # we ignore lines not in JSON format
            #print(line)
            return

        _queue.put({identifier : data})
        #print( "%f %s queue size %d" % (timestamp, identifier, _queue.qsize() ))
