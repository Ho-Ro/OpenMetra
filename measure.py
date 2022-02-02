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

import OpenMetra


# Create the parser
my_parser = argparse.ArgumentParser(description='Get data from Gossen METRAHit 29S')

# Add the arguments

my_parser.add_argument('-c',
                       '--csv',
                       action = 'store_true',
                       help = 'create csv (together with -t and/or -u)')
my_parser.add_argument('-d',
                       '--duration',
                       action = 'store',
                       dest = 'seconds',
                       type = float,
                       default = 0,
                       help = 'measure for a defined duration' )
my_parser.add_argument('-g',
                       '--german',
                       action = 'store_true',
                       help = 'use comma as decimal separator, semicolon as field separator')
my_parser.add_argument('-o',
                       '--overload',
                       dest = 'print_overload',
                       action = 'store_true',
                       help = 'print OL values as NaN instead of skipping')
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
                       help = 'add verbosity')

# parse my argument
args = my_parser.parse_args()


# open connection to a Gossen Metrahit device
with OpenMetra.OpenMetra() as mh:

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

    while True: # measurement loop
        try:
            value = mh.get_measurement()
            measure_time =  time.time() - start_time

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
