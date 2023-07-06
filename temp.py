#!/usr/bin/env python3

import argparse
import Adafruit_DHT as dht
from disco import MetricsPublisher
from enum import Enum
import sys
import time


class TempSensor(object):

    DEFAULT_TYPE = 22
    DEFAULT_TIMEOUT = 60

    def __init__(self, **kwargs):
        self.pin = kwargs["pin"]
        self.type = kwargs.get("type", TempSensor.DEFAULT_TYPE)
        self.timeout = kwargs.get("timeout", TempSensor.DEFAULT_TIMEOUT)
        self.timestamp = 0

    def update(self):
        humidity, temp = dht.read_retry(self.type, self.pin, 3, 2)

        if temp and humidity:
            self.temp = TempSensor.c2f(temp)
            self.humidity = humidity
            self.timestamp = time.time()
        elif (time.time() - self.timestamp) > self.timeout:
            raise RuntimeError("Error reading DHT sensor")

    def read(self, update=True):
        if update:
            self.update()
        return round(self.temp, 4), round(self.humidity, 4)

    @staticmethod
    def c2f(c: float):
        return (c * 9/5) + 32


def configure():
    parser = argparse.ArgumentParser(description="DHT sensor reader")
    parser.add_argument("-p", "--pin", type=int, required=True)
    parser.add_argument("-t", "--type", type=int, choices=[11, 22], default=TempSensor.DEFAULT_TYPE)
    parser.add_argument("-T", "--timeout", type=int, default=TempSensor.DEFAULT_TIMEOUT)
    parser.add_argument("--temperature-name", default="temperature")
    parser.add_argument("--humidity-name", default="humidity")
    return parser.parse_args()


def main():
    args = configure()

    metrics = MetricsPublisher()
    sensor = TempSensor(**vars(args))
    temp, humidity = sensor.read()

    print(f"{temp}° {humidity}%")
    metrics.publish({args.temperature_name: temp, args.humidity_name: humidity})


if __name__ == "__main__":
    sys.exit(main())
