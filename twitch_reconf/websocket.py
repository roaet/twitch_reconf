import logging

import obswebsocket
from obswebsocket import requests as R

LOG = logging.getLogger(__name__)


class ConfigurerOBSWebSocket(object):
    def __init__(self, debug, host, port, secret):
        self.debug = debug
        self.client = obswebsocket.obsws(host, port, secret)

    def connect(self):
        self.client.connect()

    def disconnect(self):
        self.client.disconnect()

    def get_version(self):
        return self.client.call(R.GetVersion()).getObsWebsocketVersion()
