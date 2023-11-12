#!/usr/bin/env python

from relay import Relay
import sys

args = {
  "pin": 15,
  "name": "garage_door",
  "delay": 1
}

with Relay(**args) as garage_door:
    garage_door.toggle()
    sys.exit(0)
