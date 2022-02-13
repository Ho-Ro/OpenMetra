#!/usr/bin/python

# switch the meter on, set measurement rate and enable send mode

import sys
import time
import argparse

from openmetra import OpenMetra

# Create the parser
ap = argparse.ArgumentParser(description='Get data from Gossen METRAHit 29S')

# Add the arguments

ap.add_argument('-d',
                '--device',
                action = 'store',
                dest = 'serial_device',
                default = '/dev/ttyUSB0',
                help = 'device path of serial interface, default is "/dev/ttyUSB0"' )
ap.add_argument('-o',
                '--on-off',
                dest = 'on_off',
                action = 'store_true',
                help = 'switch meter automatically on/off')
ap.add_argument('-r',
                '--rate',
                action = 'store',
                type = int,
                dest = 'rate',
                default = 9,
                help = 'set index for measurement rate: 0..5: 50 ms, 6:0.1s, 7:0.2s, 8:0.5s, 9:1s, '
                '10:2s, 11:5s, 12:10s, 13:20s, 14:30s, 15:1min, 16:2min, 17:5min, 18:10min, ..., default = 9 (1s)' )

# parse my argument
options = ap.parse_args()

with OpenMetra() as mh: # open connection to '/dev/ttyUSB0', the serial path can be an optional parameter
    if mh is None:      # could not conect
        print( 'connect error', file=sys.stderr)
        sys.exit()

    try:
        mh.wakeup()

        mh.send_command( mh.CMD_FW_STATUS )
        mh.decode( mh.get_cmd_response(), sys.stderr ) #
        time.sleep( 0.1 )

        # mh.send_command( 4, 0, 0, 0, 0, 3, 0, 4, 1, 1 ) # set time 11:40:30.00
        # mh.send_command( 4, 1, 0, 0, 2, 1, 2, 0, 2, 2 ) # set date 11:02:22
        # mh.send_command( 5, 0 ) # get real time
        # mh.send_command( 5, 1 ) # get real date
        # mh.decode( mh.get_cmd_response(), sys.stderr ) #
        # time.sleep( 0.1 )

        # rate <=5: 0.05s, 6: 0.1s, 7:0.2s, 8:0.5s - FAST MODE
        # 9:1s, 10: 2s, 11:5s, 12:10s, 13:20s, 14:30s, 15:60s, 16:2min, 17:5min, 18:10min,  (TODO: check 20, 30, 60 min, ... ?)
        rate = options.rate
        mh.send_command( 4, 2, rate )
        # mh.decode( mh.get_cmd_response(), sys.stderr ) #
        time.sleep( 0.1 )
        mh.flush_input()

        mh.set_mode( mh.MODE_SEND ) # switch to send mode
        time.sleep( 0.1 )
        mh.flush_input()

    except KeyboardInterrupt:           # ^C pressed, stop measurement
        print( '' )

