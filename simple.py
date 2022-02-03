#!/usr/bin/python

# simple demo for the usage of module OpenMetra

import sys

from openmetra import OpenMetra


with OpenMetra() as mh:           # open connection
    if mh is None:                          # check
        print( 'connect error', file=sys.stderr)
        sys.exit()
    while True:                             # run forever, stop with ^C
        try:
            print( mh.get_measurement() )   # print numeric value
        except KeyboardInterrupt:           # ^C pressed, stop measurement
            print()
            break                           # exit


