#!/usr/bin/python

# simple demo for the usage of module OpenMetra

import sys

from openmetra import OpenMetra


with OpenMetra() as mh: # open connection to '/dev/ttyUSB0', the serial path can be an optional parameter
    if mh is None:      # could not conect
        print( 'connect error', file=sys.stderr)
        sys.exit()
    while True:                           # run forever, stop with ^C
        try:
            print( mh.get_measurement() ) # print numeric value
        except KeyboardInterrupt:         # ^C pressed, stop measurement
            print()
            break                         # exit


