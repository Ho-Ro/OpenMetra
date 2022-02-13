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

    METRAHIT29S = 0x0E

    _known_devices = [ 0x0E ]  # METRAHit 29s, add other similar devices, e.g. 0x0C for 28s
    _serial_device = ''         # serial device
    _timeout = 10               # seriel timeout
    _BD232 = None               # serial object for interface
    _model = 0                  # detected model, e.g. 0x0E for 29s
    _start = 0                  # storage for detected start byte
    _unexpected_start = False   # start byte was seen during data input
    _num_digits = 0             # either 5 (fast mode) or 6 (slow)
    _digits = []                # 5 or 6 display digits
    _rs = 0                     # range & sign
    _rs_string = ''             # ... same as string
    _dp = 0                     # range (position of decimal point)
    _sign = 0                   # sign
    _ctmv = None                # Current type and measured variable
    _special = 0                # Fuse, LowBat, etc.
    _special_string = ''        # ... same as string
    _unit = ''                  # unit string (SI)
    _unit_long = ''             # unit string (with explanation, e.g. AC, DC, etc.)
    _value = ''                 # value string
    _rate = 0                   # measurement rate
    _verbose = 0                # debugging level

    _units = ['', 'V_DC', 'V_ACDC', 'V_AC',     # 0x00 .. 0x03
        'mA_DC', 'mA_ACDC', 'A_DC', 'A_ACDC',   # 0x04 .. 0x07
        'kOhm', 'nF', 'dBV', 'Hz',              # 0x08 .. 0x0B
        'Hz', 'W', 'W', 'V_diode',              # 0x0C .. 0x0F
        'V_diode', '0x11', '°C', '0x13',        # 0x10 .. 0x13
        '0x14', '0x15', '0x16', '0x17',         # 0x14 .. 0x17
        '0x18', '0x19', '0x1A', 'mA',           # 0x18 .. 0x1B
        'A', 'V', '0x1E', '0x1F',               # 0x1C .. 0x1F
    ]

    CMD_FW_STATUS = 3
    CMD_MODE = 6
    CMD_MEASURE = 8

    MODE_NORMAL = 0
    MODE_SEND = 1
    MODE_OFF = 5
    MODE_RESET = 6



    #######################
    # the class interface #
    #######################

    def __init__( self, serial_device = '/dev/ttyUSB0', timeout = 10, known_devices = [ 0x0E ]  ):
        'Init internal data, e.g. the name of serial device'
        self._serial_device = serial_device
        self._known_devices = known_devices
        self._timeout = timeout


    def __del__( self ):
        self.close()


    def __enter__( self ):
        '''Automatically called at object entry via "with"
        Open the serial object and return "self" on success, "None" on error'''
        return self.open()


    def __exit__(self, ctx_type, ctx_value, ctx_traceback):
        'Automatically called et object exit via "with", clean up'
        self.close()


    def open( self, timeout=10 ):
        '''Open the serial connection and return "self" on success, "None" on error'''
        try:
            # open connection to BD232 interface
            self._BD232 = serial.Serial( self._serial_device, baudrate = 9600, timeout = timeout )
        except:
            return None
        else:
            time.sleep( .1 )
            self.flush_input()
        return self


    def close( self ):
        'Close the connection to the meter, i.e. the serial object'
        if self._BD232:
            self._BD232.close()
        self._BD232 = None


    def flush_input( self ):
        'Remove all pending input'
        self._BD232.flushInput()


    def wakeup( self ):
        'Send serial data to switch the meter on'
        self._BD232.write( bytearray( 42 ) )
        time.sleep( 1 )
        self.flush_input()


    def set_timeout( self, timeout=10 ):
        self._BD232.timeout( timeout )


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


    def get_special_string( self ):
        'Return the status bits as string'
        return self._decode_special()


    def get_rs_string( self ):
        'Return range and sign as string'
        return self._decode_rs()


    ######################
    # internal functions #
    ######################

    def _get_value( self ):
        'Internal function to get status and measurement value from Metrahit device'
        if self._start >= 0x10:                         # we know that we're in fast mode
            slow = False
        else:                                           # can be fast or slow mode, table TM1 1b) or 2)
            self._model = self._start                   # byte 1: remember device model
            # 4 status bytes with info in low 4 bits
            self._ctmv = self._get_digit()              # byte 2: type index lsb
            self._special = self._get_digit()           # byte 3: xxxxZBLF (Zero, Beep, LowBat, Fuse)
            self._special += (self._get_digit()) << 4   # byte 4: xxxxMxxD (Man, Data)
            self._rs = self._get_digit()                # byte 5: range and sign
            self._dp = self._rs & 0x7                   #  - decimal position 0..7
            self._sign = self._rs & 0x8                 #  - sign
            byte_6 = self._get_byte()
            if self._unexpected_start:
                return False
            if byte_6 >= 0x30:                          # ok, slow mode, stay in table TM1 2)
                slow = True
            else:                                       # change to table TM1 1a)
                slow = False

        if slow:
            # we are in "slow mode", get 6 data digits (low 4 bits)
            byte_6 &= 0x0F
            self._digits = [ byte_6 ]                   # 1st byte already received (in start)
            self._OL = byte_6 >= 10                     # overload detection
        else:
            # we are in "fast mode", get 5 data digits (low 4 bits)
            self._digits = []
            self._OL = False

        for p in range( 5 ):                            # fast: bytes 0..4 or slow: bytes 1..5
            digit = self._get_digit()
            if digit >= 10:
                self._OL = True
            else:
                self._digits.append( digit )

        if self._unexpected_start:
            return False

        if slow:                                        # fetch byte 12 and 13 of TM1 2)
            self._ctmv += (self._get_digit()) << 4      # type index msb
            self._rate = self._get_digit()              # send intervall, 4: 1s
            if self._unexpected_start:
                return False
            if self._verbose > 1:
                print( 'SLOW:', self._ctmv, hex(self._special), self._dp, self._sign, self._rate )
        elif self._verbose > 1:
            print( 'FAST:', self._ctmv, hex(self._special), self._dp, self._sign )

        if self._verbose > 2:
            print( 'DIGITS:', self._digits )

        self.decode_unit()
        self._adjust_dp()
        self._format_number()
        return self._value


    def _start_detected( self ):
        'Check for start condition 0x0E'
        self._start = self._get_byte()
        self._unexpected_start = False
        return ( self._start in self._known_devices ) or ( self._start & 0x30 == 0x10 )


    def _get_byte( self ):
        'Wait for next byte (with timeout)'
        byte = self._BD232.read()
        if not len( byte ):
            sys.stderr.write( 'Timeout (Enable transfer: hold down "DATA/CLEAR" while switching on)\n' )
            sys.exit()
        byte = ord( byte ) & 0x3F
        if self._verbose > 3:
            print( '_get_byte', hex( byte ) )
        return byte


    def _get_digit( self ):
        'Get one digit (4 MSB = 0)'
        byte = self._get_byte()
        if byte < 0x30:
            self._unexpected_start = True
        return byte & 0x0F


    def decode_unit( self, ctmv=None ):
        'Prepare unit string'
        if ctmv is None:
            ctmv = self._ctmv
        if ctmv is None:
            # not yet seen (fast mode)
            self._unit = ''
            self._unit_long = ''
            return ''
        if ctmv < len( self._units ):
            self._unit_long = self._units[ ctmv ]
            self._unit = self._unit_long.split('_')[0]
        else:
            self._unit = hex( ctmv )
            self._si_unit = hex( ctmv )
        return self._unit


    def _adjust_dp( self ):
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
            for p in range( len( self._digits ) ):
                if self._dp == p:
                    self._value += '.'
                self._value += chr( self._digits[ self._num_digits - 1 - p ] + ord( '0' ) )


    def _decode_rs( self ):
        if self._special is None: # not yet seen (fast mode)
            return ''
        self._rs_string = ''
        if self._rs & 0x08:
            self._rs_string += '-'
        else:
            self._rs_string += '+'
        self._rs_string += str( self._rs & 0x07 )
        return self._rs_string


    def _decode_special( self ):
        'Prepare special string'
        self._special_string = ''
        if self._special is None: # not yet seen (fast mode)
            return ''
        if self._special & 0x80:
            self._special_string += 'M'
        else:
            self._special_string += '.'
        self._special_string += '..'
        if self._special & 0x10:
            self._special_string += 'D'
        else:
            self._special_string += '.'
        if self._special & 0x08:
            self._special_string += 'Z'
        else:
            self._special_string += '.'
        if self._special & 0x04:
            self._special_string += 'B'
        else:
            self._special_string += '.'
        if self._special & 0x02:
            self._special_string += 'L'
        else:
            self._special_string += '.'
        if self._special & 0x01:
            self._special_string += 'F'
        else:
            self._special_string += '.'
        return self._special_string


    def set_mode( self, mode ):
        self.send_command( self.CMD_MODE, mode, mode )


    def set_rate( self, rate_index=9 ):
        rates = [.05, .05, .05, .05, .05, .05, .1, .2,   # 0..7
                .5, 1, 2, 5, 10, 20, 30, 60,            # 8..15
                120, 300, 600, 1200, 1800, 3600         # 16..21
        ]
        self.send_command( 4, 2, rate_index )
        if rate_index > 11 and rate_index < len( rates ):
            self._BD232.timeout = 2 * rates[ rate_index ]


    def send_command( self, cmd, p0=0, p1=0x3F, p2=0x3F, p3=0x3F, p4=0x3F, p5=0x3F, p6=0x3F, p7=0x3F, p8=0x3F ):
        data = bytearray()
        data.append( 0x03 ) # addr<<2 | 0x03
        data.append( 0x2b ) # +
        data.append( 0x3f ) # ?
        data.append( cmd ) #
        data.append( p0 ) #
        data.append( p1 ) #
        data.append( p2 ) #
        data.append( p3 ) #
        data.append( p4 ) #
        data.append( p5 ) #
        data.append( p6 ) #
        data.append( p7 ) #
        data.append( p8 ) #

        data = self._chksum_14( data )
        data = self._encode_14_to_42( data )
        self._BD232.write( data )


    def _chksum_14( self, data ):
        chs = 0
        ba = bytearray()
        for n in range( 13 ):
            b = data[ n ]
            chs += b
            ba.append( b )
        chs = (64 - chs) & 0x3F
        ba.append( chs )
        return ba


    def _encode_14_to_42( self, data ):
        buf = bytearray()
        for n in range( 14 ):
            mask = 0x01
            for m in range( 3 ):
                a = b = 0
                if data[ n ] & mask:
                    a = 0x0f
                mask <<= 1
                if data[ n ] & mask:
                    b = 0xf0
                mask <<= 1
                buf.append( a | b )
        return buf


    def get_cmd_response( self ):
        response = self._BD232.read( 14 )
        return response


    def decode( self, rsp, outfile=sys.stdout ):
        if rsp[3] & 0x3F == 3:
            return self._decode3( rsp, outfile )
        elif rsp[3] & 0x3F == 8:
            return self._decode8( rsp, outfile )
        for b in rsp:
            d = b & 0x3F
            print( hex( d ), d, file=outfile )


    def _decode3( self, rsp, outfile=sys.stdout ):
        functions = [ '', 'AUTO', 'V_AC', 'V_ACDC', 'V_DC', 'Ohm', 'Diode', '°C', 'F', 'mA', 'A' ]
        print( 'FW ver : ', rsp[5] & 0x3F, '.', rsp[4] & 0x3F, sep='', file=outfile )
        model = rsp[12] & 0x3F
        switch = rsp[6] & 0x3F
        if self.METRAHIT29S == model:
            model = 'METRAHit 29S'
        print( 'Model  :', model, file=outfile )
        print( 'Switch :', functions[ switch ], file=outfile )
        print( 'Battery:', round( (rsp[11] & 0x3F) * 0.1, 1 ) , 'V', file=outfile )


    def _decode8( self, rsp, outfile=sys.stdout ):
        if rsp[3] & 0x3F == 8:
            value = 0
            mul = 1
            for b in rsp[7:13]:
                d = b & 0x3F
                print( d, file=outfile )
                value += d * mul
                mul *= 10
            print( 'Value:', value, file=outfile )
            function = rsp[5] & 0x3F
            print( 'Function:', self.decode_unit( function ), file=outfile )
            print( 'Range:', rsp[6] & 0x0F, (rsp[6] & 0x10) >> 4, file=outfile  )


'''
response to cmd3: 4=fwmin, 5:fwmax, 6:switchpos, 7:fkt, 8:range, 9,10:?, 11:ubat*10, 12:model, 13:chksum
response to cmd8: 5:fkt, 6:status, 7..12 digits, 13:chksum
'''


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
