#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Get measurement data from multimeter Gossen METRAHit 29S via BD232 serial interface.
The BD232 is powered by the RTS and DTR serial lines.
Works with FTDI RS232 USB connection to /dev/ttyUSB0 (linux).
Format is 9600 Bd, 8 bits + Start + Stop bit (only lower 6 bits are used.
Activate the transmission with: 'SEt v SEnd <-/ OFF v on <-/',
or at switch-on by depressing <DATA/CLEAR> and <ON> button together.
Rate of data beeing sent into interface depends on item 'rAtE' set in menu.

Protocol definition:

Measured data with fast rate (rate 50 ms, V_DC, A_DC only)
-----------------------------------------------
|Byte| Output unit Bit0..Bit3       |Bit5|Bit4|
|----|------------------------------|----|----|
|  1 | Measuring range, sign        |  0 |  1 |
|  2 | Units                        |  1 |  1 |
|  3 | Tens                         |  1 |  1 |
|  4 | Hundreds                     |  1 |  1 |
|  5 | Thousands                    |  1 |  1 |
|  6 | TenThousands                 |  1 |  1 |
-----------------------------------------------

Instruments setting with fast rate (sent at lower rate of ~ 500 ms)
-----------------------------------------------
|Byte| Output unit Bit0..Bit3       |Bit5|Bit4|
|----|------------------------------|----|----|
|  1 | Device code, 1110 is 29s     |  0 |  0 |
|  2 | Curr. type, meas. variable 1 |  1 |  1 |
|  3 | Special character 1          |  1 |  1 |
|  4 | Special character 2          |  1 |  1 |
|  5 | Measuring range, sign 1      |  1 |  1 |
-----------------------------------------------

Ranges: V AC, V AC+DC, I AC+DC, Ohm, Ohm with buzzer, F, Hz , Temp., dB,
V-diode, V-diode with buzzer, Events, Counter, Mains analysis and Power.
Also V DC, A DC and functions when send interval >50 ms.
-----------------------------------------------
|Byte| Output unit Bit0..Bit3       |Bit5|Bit4|
|----|------------------------------|----|----|
|  1 | Device code, 1110 is 29s     |  0 |  0 |
|  2 | Curr. type, meas. variable 1 |  1 |  1 |
|  3 | Special character 1          |  1 |  1 |
|  4 | Special character 2          |  1 |  1 |
|  5 | Measuring range, sign        |  1 |  1 |
|  6 | Units                        |  1 |  1 |
|  7 | Tens                         |  1 |  1 |
|  8 | Hundreds                     |  1 |  1 |
|  9 | Thousands                    |  1 |  1 |
| 10 | TenThousands                 |  1 |  1 |
| 11 | HundredThousands             |  1 |  1 |
| 12 | Curr. type, meas. variable 2 |  1 |  1 |
| 13 | Send interval                |  1 |  1 |
-----------------------------------------------
29S: In case of power measurement there are sent 3 of these blocks
with delay 200 ms in order power - W, voltage - V, current - A.
See also:
https://www.mikrocontroller.net/attachment/22868/22SM-29S_Interface_Protocol1.pdf
'''

import serial;
import sys;
import time;


class OpenMetra:
    'Gossen METRAHit 29s data transfer via BD232 interface'

    #######################
    # the class variables #
    #######################

    _known_devices = [ 0x0E ]   # METRAHit 29s, add other similar devices, e.g. 0x0C for 28s
    _serial_device = ''         # serial device
    _BD232 = None               # serial object for interface
    _model = 0                  # detected model, e.g. 0x0E for 29s
    _num_digits = 0             # either 5 (fast mode) or 6 (slow)
    _digits = []                # 5 or 6 display digits
    _dp = 0                     # position of decimal point
    _sign = 0                   # sign
    _ctmv = None                # Current type and measured variable
    _special = 0                # Fuse, LowBat, etc.
    _unit = ''                  # unit string (SI)
    _unit_long = ''             # unit string (with explanation, e.g. AC, DC, etc.)
    _value = ''                 # value string
    _rate = 0                   # measurement rate
    _verbose = 0                # debugging level


    #######################
    # the class interface #
    #######################

    def __init__( self, serial_device = '/dev/ttyUSB0', known_devices = [ 0x0E ] ):
        'Init internal data, e.g. the name of serial device'
        self._serial_device = serial_device
        self._known_devices = known_devices


    def __del__( self ):
        self.close()


    def __enter__( self ):
        '''Automatically called at object entry via "with"
        Open the serial object and return "self" on success, "None" on error'''
        return self.open()


    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        'Automatically called et object exit via "with", clean up'
        self.close()


    def open( self ):
        '''Open the serial connection and return "self" on success, "None" on error'''
        try:
            # open connection to BD232 interface
            self._BD232 = serial.Serial( self._serial_device, baudrate = 9600, timeout = 10 )
        except:
            return None
        else:
            time.sleep( .1 )
            self._BD232.flushInput()
        return self


    def close( self ):
        'Close the connection to the meter, i.e. the serial object'
        if self._BD232:
            self._BD232.close()
        self._BD232 = None


    def set_verbose( self, verbose ):
        'Set the verbosity level for debugging'
        self._verbose = verbose


    def get_measurement( self, format_value=False ):
        'Wait for one measurement and return the value as string'
        # wait for start condition
        while not self._start_detected():
            pass
        if format_value:
            return str( float( self._get_value() ) )
        else:
            return self._get_value()


    def get_unit( self ):
        'Return the SI unit string of last measurement'
        return self._unit


    def get_unit_long( self ):
        'Return the long unit string (with explanation, e.g. AC, DC, etc.) of last measurement'
        return self._unit_long


    ######################
    # internal functions #
    ######################

    def _get_value( self ):
        'Internal function to get status and measurement value from Metrahit device'
        if self._start < 0x10:                           # Device code, either "slow mode" or "fast config"
            self._model = self._start                    # remember device model
            if self._model not in self._known_devices:
                return None
            # 4 status bytes with info in low 4 bits
            self._ctmv = self._get_digit()               # byte 1: type index lsb
            self._special = self._get_digit()            # byte 2: xxxxZBLF (Zero, Beep, LowBat, Fuse)
            self._special += (self._get_digit()) << 4    # byte 3: xxxxMxxD (Man, Data)
            self._rs = self._get_digit()                 # byte 4: range and sign
            self._dp = self._rs & 0x7               #  - decimal position 0..7
            self._sign = self._rs & 0x8                  #  - sign

            last_start = self._start                     # next byte will be either data digit or new start
            if self._start_detected():                   # start condition detected, it was "fast config"
                self._rate = 0
                if self._verbose:
                    print( 'FAST:', hex(last_start), self._ctmv, hex(self._special), self._dp, self._sign, file=sys.stderr )
                return self._get_value()                 # get 2nd part (fast data)

            # we are in "slow mode", get 6 data digits (low 4 bits)
            self._num_digits = 6
            first = self._start & 0x0F
            self._digits = [ first ]                     # 1st byte already received (in start)
            self._OL = first >= 10                       # overload detection
            for p in range( 1, self._num_digits ):       # bytes 2..6: 6 digits value
                digit = self._get_digit()
                if digit >= 10:
                    self._OL = True
                else:
                    self._digits.append( digit )

            self._ctmv += (self._get_digit()) << 4        # type index msb
            self._rate = self._get_digit()                # send intervall, 4: 1s

            if self._verbose:
                print( 'SLOW:', hex(last_start), self._ctmv, hex(self._special), self._dp, self._sign, self._rate, file=sys.stderr )

        else: # 0x1x: fast data mode
            self._rs = self._start & 0x0F
            self._dp = self._rs & 0x7                     #  - decimal position 0..7
            self._sign = self._rs & 0x8                   #  - sign
            self._digits = []
            self._OL = False                              # overload detection
            self._num_digits = 5
            for p in range( self._num_digits ):           # bytes 1..5: 5 digits value
                digit = self._get_byte() & 0x0F
                if digit >= 10:
                    self._OL = True
                else:
                    self._digits.append( digit )

        if self._verbose > 1:
            print( 'DIGITS:', self._digits, file=sys.stderr )

        self._decode_unit()
        self._format_number()
        return self._value

    def _start_detected( self ):
        'Check for start condition'
        self._start = self._get_byte()
        return self._start & 0x30 != 0x30


    def _get_byte( self ):
        'Wait for next byte (with timeout)'
        byte = self._BD232.read()
        if not len( byte ):
            sys.stderr.write( 'Timeout (Enable transfer: hold down "DATA/CLEAR" while switching on)\n' )
            sys.exit()
        byte = ord( byte ) & 0x3F
        if self._verbose > 2:
            print( hex( byte ), file=sys.stderr )
        return byte


    def _get_digit( self ):
        'Get one digit (4 MSB = 0)'
        return self._get_byte() & 0x0F


    def _decode_unit( self ):
        'Prepare unit string, correct decimal point position'

        if self._ctmv is None: # not yet seen (fast mode)
            return

        units = ['', 'V_DC', 'V_ACDC', 'V_AC',          # 0x00 .. 0x03
                 'mA_DC', 'mA_ACDC', 'A_DC', 'A_ACDC',  # 0x04 .. 0x07
                'kOhm', 'nF', 'dBV', 'Hz',              # 0x08 .. 0x0B
                'Hz', 'W', 'W', 'V_diode',              # 0x0C .. 0x0F
                'V_diode', '0x11', '°C', '0x13',        # 0x10 .. 0x13
                '0x14', '0x15', '0x16', '0x17',         # 0x14 .. 0x17
                '0x18', '0x19', '0x1A', 'mA',           # 0x18 .. 0x1B
                'A', 'V', '0x1E', '0x1F',               # 0x1C .. 0x1F
        ]

        if self._ctmv < len( units ):
            self._unit_long = units[ self._ctmv ]
            self._unit = self._unit_long.split('_')[0]
        else:
            self._unit = hex( self._ctmv )
            self._si_unit = hex( self._ctmv )

        # reported decimal point position must be corrected for some ranges
        # in fast mode these values are not correct up to 500 ms after start!
        if self._ctmv == 0x06:   # A_DC
            self._dp += 1
        elif self._ctmv == 0x07: # A_ACDC
            self._dp += 1
        elif self._ctmv == 0x09: # nF
            self._dp += 1
        elif self._ctmv == 0x0A: # dBV
            self._dp = 3    # dBV decimal is always three!
        elif self._ctmv == 0x0D: # W on mA range
            self._dp -= 2
        elif self._ctmv == 0x0E: # W on A range
            self._dp -= 2
        elif self._ctmv == 0x12: # can also be Fahrenheit (?)
            self._dp += 4
        elif self._ctmv == 0x1C: # A in power mode
            self._dp += 1


    def _format_number( self ):
        'Prepare number string with sign and decimal point'
        if self._OL:
            self._value = None
        else:
            self._value = ''
            if self._sign:
                self._value += '-'

            if self._dp < 0:                    # special treatment e.g. for power modes
                self._value += '.'              # start with decimal point
                self._value += -self._dp * '0'  # add some leading zeros
            # reverse digit order
            for p in range( self._num_digits ):
                if self._dp == p:
                    self._value += '.'
                self._value += chr( self._digits[ self._num_digits - 1 - p ] + ord( '0' ) )



########################################################
# minimal class invocation example with error handling #
########################################################

if __name__ == "__main__":
    with OpenMetra() as mh:                     # open connection
        if mh is None:                          # check
            print( 'connect error', file=sys.stderr)
            sys.exit()
        while True:                             # run forever, stop with ^C
            try:
                print( mh.get_measurement() )   # print numeric value
            except KeyboardInterrupt:           # ^C pressed, stop measurement
                print()
                break                           # exit
