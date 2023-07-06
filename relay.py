#!/usr/bin/env python3

import argparse
from disco import MetricsPublisher
from enum import Enum
import RPi.GPIO as gpio
import os
import sys
import time


class RelayCommand(Enum):
    open = "open"
    close = "close"
    toggle = "toggle"

    def __str__(self):
        return self.value


class Relay(object):
    def __init__(self, **kwargs):
        self.pin = kwargs["pin"]
        self.delay = kwargs.get("delay", 1)
        gpio.setmode(gpio.BOARD)
        gpio.setwarnings(False)
        gpio.setup(self.pin, gpio.OUT)

    def open(self):
        gpio.output(self.pin, gpio.HIGH)

    def close(self):
        gpio.output(self.pin, gpio.LOW)

    def toggle(self, delay=None):
        self.close()
        time.sleep(delay or self.delay)
        self.open()

    def run(self, command: RelayCommand):
        if command == RelayCommand.open:
            self.open()
        elif command == RelayCommand.close:
            self.close()
        elif command == RelayCommand.toggle:
            self.toggle()
        else:
            raise ValueError(f"Invalid relay command: {command}")

    def __enter__(self):
        return self

    def __exit__(self, type_, value, trace):
        gpio.cleanup()


class RemoteRelay(Relay):
    REMOTE_ENDPOINT = f"ipc:///var/tmp/remote_relay.{os.getpid()}"

    def __init__(self, **kwargs):
        self.context = zmq.Context()
        self.endpoint = kwargs.get("endpoint", REMOTE_ENDPOINT)
        super.__init__(kwargs)

    def controller(self):
        socket = self.context.socket(zmq.ROUTER)
        socket.bind(self.endpoint)

        while True:
            env, _, msg = socket.recv_multipart()
            command = msg.decode()

            try:
                self.run(command)
            except ValueError as e:
                print(str(e), file=sys.stderr)

    def open(self):
        self.send(RelayCommand.open)

    def close(self):
        self.send(RelayCommand.close)

    def toggle(self):
        self.send(RelayCommand.toggle)

    def send(self, command: RelayCommand):
        socket = self.context.socket(zmq.REQ)
        socket.connect(self.endpoint)
        socket.send_string(command.name)


def configure():
    parser = argparse.ArgumentParser(description="GPIO relay control")
    parser.add_argument("command", type=RelayCommand, choices=list(RelayCommand))
    parser.add_argument("-p", "--pin", type=int, required=True)
    parser.add_argument("-d", "--delay", type=int, default=1)
    parser.add_argument("--relay-name", default="relay")
    return parser.parse_args()


def main():
    args = configure()
    
    metrics = MetricsPublisher()
    relay = Relay(**vars(args))
    relay.run(args.command)

    metrics.publish({args.relay_name: str(args.command)})


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)
