# -*- coding: utf-8 -*-

import base64
import logging
import socket
import time
import codecs
import threading
import sys
from . import exceptions
from . import upnp
from .utils import LogIt, LogItWithReturn

logger = logging.getLogger('samsungctl')


class RemoteLegacy(upnp.UPNPTV):
    """Object for remote control connection."""

    @LogIt
    def __init__(self, config):
        """Make a new connection."""
        self.sock = None
        self.config = config
        self._starting = True
        self._thread = None
        self._loop_event = threading.Event()
        self._receive_lock = threading.Lock()

        super(RemoteLegacy, self).__init__(config.host, config.upnp_locations)

    @property
    @LogItWithReturn
    def power(self):
        return self.sock is not None

    @power.setter
    @LogIt
    def power(self, value):
        if value and not self.power:
            logger.info('Power on is not supported for legacy TV\'s')
        elif not value and self.power:
            event = threading.Event()
            while self.power:
                self.control('KEY_POWEROFF')
                event.wait(2.0)

    def loop(self):
        while not self._loop_event.isSet():
            try:
                data = self.sock.recv(2048)
                if data:
                    self._read_response(data)
                self._loop_event.wait(0.2)

            except socket.error:
                self.sock = None
                self.disconnect()

                while self.sock is None and not self._loop_event.isSet():
                    try:
                        self.open()
                    except:
                        self._loop_event.wait(2.0)

                if not self._loop_event.isSet():
                    self.connect()

        self._thread = None
        self._loop_event.clear()

    @LogIt
    def open(self):
        self._starting = True
        self.config.port = 55000

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if self.config.timeout:
            self.sock.settimeout(self.config.timeout)

        try:
            self.sock.connect((self.config.host, self.config.port))
        except socket.error:
            if not self.config.paired:
                raise RuntimeError('Unable to pair with TV.. Is the TV on?!?')
            else:
                logger.info('Is the TV on?!?')
                self.sock = None
                return

        payload = (
            b"\x64\x00" +
            self._serialize_string(self.config.description) +
            self._serialize_string(self.config.id) +
            self._serialize_string(self.config.name)
        )
        packet = b"\x00\x00\x00" + self._serialize_string(payload, True)

        logger.info("Sending handshake.")
        self.sock.send(packet)
        self._read_response(True)

        if self._thread is None:
            self._thread = threading.Thread(target=self.loop)
            self._thread.start()

        self._starting = False

    @LogIt
    def close(self):
        """Close the connection."""
        self._loop_event.set()
        if self._thread is not None:
            self._thread.join(2.0)

        if self.sock:
            self.sock.close()
            self.sock = None
            logging.debug("Connection closed.")

    @LogIt
    def control(self, key):
        """Send a control command."""
        if self.sock is None:
            logger.info('Is the TV on?!?')
            return

        with self._receive_lock:
            payload = b"\x00\x00\x00" + self._serialize_string(key)
            packet = b"\x00\x00\x00" + self._serialize_string(payload, True)

            logger.info("Sending control command: %s", key)
            self.sock.send(packet)
            time.sleep(self._key_interval)

    _key_interval = 0.2

    @LogIt
    def _read_response(self, first_time=False):
        header = self.sock.recv(3)
        tv_name_len = int(codecs.encode(header[1:3], 'hex'), 16)
        tv_name = self.sock.recv(tv_name_len)

        if first_time:
            logger.debug("Connected to '%s'.", tv_name.decode())

        response_len = int(codecs.encode(self.sock.recv(2), 'hex'), 16)
        response = self.sock.recv(response_len)

        if len(response) == 0:
            self.close()
            raise exceptions.ConnectionClosed()

        if response == b"\x64\x00\x01\x00":
            logger.debug("Access granted.")
            self.config.paired = True
            return
        elif response == b"\x64\x00\x00\x00":
            raise exceptions.AccessDenied()
        elif response[0:1] == b"\x0a":
            if first_time:
                logger.warning("Waiting for authorization...")
            return self._read_response()
        elif response[0:1] == b"\x65":
            logger.warning("Authorization cancelled.")
            raise exceptions.AccessDenied()
        elif response == b"\x00\x00\x00\x00":
            logger.debug("Control accepted.")
            return

        raise exceptions.UnhandledResponse(response)

    @staticmethod
    @LogItWithReturn
    def _serialize_string(string, raw=False):
        if isinstance(string, str):
            if sys.version_info[0] > 2:
                string = str.encode(string)

        if not raw:
            string = base64.b64encode(string)

        return bytes([len(string)]) + b"\x00" + string
