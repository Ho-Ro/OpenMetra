#!/usr/bin/python
# -*- coding: utf-8 -*-

# get measement from multimeter Gossen METRAHit 29S via BD232 serial interface
# works with FTDI RS232 USB connection to /dev/ttyUSB0
# switch on with: SEt v SEnd <-/ OFF v on <-/
# or by holding DATA/CLEAR while switching on the instrument
# the meter sends the measurement as 4bit digits with a rate of 9600 bit/s
# the BD232 is powered by the RTS and DTR lines

import sys
import time
import argparse

from openmetra import OpenMetra


# Create the parser
my_parser = argparse.ArgumentParser(description='Get data from Gossen METRAHit 29S')

# Add the arguments

my_parser.add_argument('-c',
                       '--csv',
                       action = 'store_true',
                       help = 'create csv (together with -t and/or -u)')
my_parser.add_argument('-g',
                       '--german',
                       action = 'store_true',
                       help = 'use comma as decimal separator, semicolon as field separator')
my_parser.add_argument('-n',
                       '--number',
                       action = 'store',
                       dest = 'number',
                       type = int,
                       default = 0,
                       help = 'get NUMBER measurement values' )
my_parser.add_argument('-o',
                       '--overload',
                       dest = 'print_overload',
                       action = 'store_true',
                       help = 'print OL values as "None" instead of skipping')
my_parser.add_argument('-s',
                       '--seconds',
                       action = 'store',
                       dest = 'seconds',
                       type = float,
                       default = 0,
                       help = 'measure for a duration of SECONDS' )
my_parser.add_argument('-t',
                       '--timestamp',
                       dest = 'print_timestamp',
                       action = 'store_true',
                       help = 'print timestamp for each value')
my_parser.add_argument('-u',
                       '--unit',
                       dest = 'print_unit',
                       action = 'store_true',
                       help = 'print unit of measured value')
my_parser.add_argument('-V',
                       action = 'count',
                       dest = 'verbose',
                       default = 0,
                       help = 'increase verbosity')

# parse my argument
args = my_parser.parse_args()


# open connection to a Gossen Metrahit device
with OpenMetra() as mh:

    if mh is None:
        print( 'connect error', file=sys.stderr)
        sys.exit()

    mh.set_verbose( args.verbose )

    start_time = time.time()

    if args.csv:
        if args.german:
            field_sep = ';'
        else:
            field_sep = ','
    else:
        field_sep = ' '

    measurement = 0
    while True: # measurement loop
        try:
            if args.number and measurement >= args.number:
                break

            value = mh.get_measurement()
            if value is None:
                if not args.print_overload:
                    continue
            measure_time =  time.time() - start_time
            measurement += 1

            if args.seconds and ( measure_time > args.seconds ): # time over
                break

            if args.print_timestamp: # seconds since start with 3 decimal digits
                timestamp = str( round( measure_time, 3 ) )
                if args.german:
                    timestamp = timestamp.replace( '.', ',' )
                print( timestamp, end = field_sep )

            if args.german:
                value = value.replace( '.', ',' )
            print( value, end = '' )

            if args.print_unit:
                print ( field_sep + mh.get_unit(), end = '' )

            print()

        except KeyboardInterrupt:
            print()
            break
