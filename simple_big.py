#!/usr/bin/python

# simple demo for the usage of module OpenMetra

import sys

from openmetra import OpenMetra


def print_big( string ):

    dot_5x8 = [
        [' ### ', '  #  ', ' ### ', ' ####', '#    ', '#####', '  ###', '#####', ' ### ', ' ### ', '     ', '     ', '     ', '     '],
        ['#   #', ' ##  ', '#   #', '    #', '#  # ', '#    ', ' #   ', '    #', '#   #', '#   #', '  #  ', '     ', '     ', '     '],
        ['#   #', '# #  ', '    #', '   # ', '#  # ', '#### ', '#    ', '    #', '#   #', '#   #', '  #  ', '     ', '     ', '     '],
        ['#   #', '  #  ', '  ## ', '  ###', '#####', '    #', '#### ', '   # ', ' ### ', ' ####', '#####', '     ', '#####', '     '],
        ['#   #', '  #  ', ' #   ', '    #', '   # ', '    #', '#   #', '  #  ', '#   #', '    #', '  #  ', '     ', '     ', '     '],
        ['#   #', '  #  ', '#    ', '#   #', '   # ', '#   #', '#   #', '  #  ', '#   #', '   # ', '  #  ', '  ## ', '     ', '  ## '],
        [' ### ', '#####', '#####', ' ### ', '   # ', ' ### ', ' ### ', '  #  ', ' ### ', '###  ', '     ', '  ## ', '     ', '  ## '],
        ['     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '   # ', '     ', '     '],
    ]

    y_size = len( dot_5x8 )
    x_size = len( dot_5x8[0][0] )

    print( chr(27) + '[2J' )
    print( chr(27) + '[H' )

    if string is None:
        return

    neg = string[0] == '-'

    for line in range( y_size ):            # rows
        if not neg:                         # leading space
            print( x_size * ' ', end = '  ' )
        for c in string:                    # columns
            n = ord( c ) - ord('0')
            if n < 0:                       # correct for '+' ',' '-' '.'
                n += 15
            print( dot_5x8[ line ][ n ], end = '  ' )
        print()
    print()


with OpenMetra() as mh:                     # open connection
    if mh is None:                          # check
        print( 'connect error', file=sys.stderr)
        sys.exit()
    while True:                             # run forever, stop with ^C
        try:
            print_big( mh.get_measurement() ) # print numeric value
        except KeyboardInterrupt:           # ^C pressed, stop measurement
            print()
            break                           # exit


