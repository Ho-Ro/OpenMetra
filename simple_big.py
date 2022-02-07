#!/usr/bin/python

# simple demo for the usage of module OpenMetra

import sys

from openmetra import OpenMetra


def print_big( string ):
    '''print numerical data with big character on top of terminal screen'''

    dor_matrix = [
        [' ### ', '  #  ', ' ### ', ' ####', '#    ', '#####', '  ###', '#####', ' ### ', ' ### ', '     ', '     ', '     ', '     '],
        ['#   #', ' ##  ', '#   #', '    #', '#  # ', '#    ', ' #   ', '    #', '#   #', '#   #', '  #  ', '     ', '     ', '     '],
        ['#   #', '# #  ', '    #', '   # ', '#  # ', '#### ', '#    ', '    #', '#   #', '#   #', '  #  ', '     ', '     ', '     '],
        ['#   #', '  #  ', '  ## ', '  ###', '#####', '    #', '#### ', '   # ', ' ### ', ' ####', '#####', '     ', '#####', '     '],
        ['#   #', '  #  ', ' #   ', '    #', '   # ', '    #', '#   #', '  #  ', '#   #', '    #', '  #  ', '     ', '     ', '     '],
        ['#   #', '  #  ', '#    ', '#   #', '   # ', '#   #', '#   #', '  #  ', '#   #', '   # ', '  #  ', '  ## ', '     ', '  ## '],
        [' ### ', '#####', '#####', ' ### ', '   # ', ' ### ', ' ### ', '  #  ', ' ### ', '###  ', '     ', '  ## ', '     ', '  ## '],
        ['     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '     ', '   # ', '     ', '     '],
    ]

    y_size = len( dor_matrix )
    x_size = len( dor_matrix[0][0] )

    print( chr(27) + '[2J' )    # clear screen
    print( chr(27) + '[H' )     # cursor home

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
            print( dor_matrix[ line ][ n ], end = '  ' )
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


