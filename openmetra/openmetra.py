#!/usr/bin/python
# -*- coding: utf-8 -*-


VERSION = '0.3.1'


import serial;
import sys;
import time;


class OpenMetra:
    '''Gossen METRAHit 29s data transfer via BD232 interface

    Get measurement data from multimeter Gossen METRAHit 29S via BD232 serial interface.
    The BD232 is powered by the RTS and DTR serial lines.
    Tested with FTDI and similar RS232 USB serial interface to "/dev/ttyUSB0" (linux),
    should also work for Windows with e.g. serial_device="COM8".
    Format is 9600 Bd, 8 bits + Start + Stop bit (only lower 6 bits are used).
    Activate the transmission with: 'SEt v SEnd <-/ OFF v on <-/',
    or at switch-on by depressing <DATA/CLEAR> and <ON> button together.
    Rate of data beeing sent into interface depends on item 'rAtE' set in menu.

    Protocol definition:

    TM1a) Measured data with fast rate (rate 50 ms, V_DC, A_DC only)
    -----------------------------------------------
    |Byte| Output unit Bit0..Bit3       |Bit5|Bit4|
    |----+------------------------------+----+----|
    |  1 | Measuring range, sign        |  0 |  1 |
    |  2 | Units                        |  1 |  1 |
    |  3 | Tens                         |  1 |  1 |
    |  4 | Hundreds                     |  1 |  1 |
    |  5 | Thousands                    |  1 |  1 |
    |  6 | TenThousands                 |  1 |  1 |
    -----------------------------------------------

    TM1b) Instruments setting with fast rate (sent at lower rate of ~ 500 ms)
    -----------------------------------------------
    |Byte| Output unit Bit0..Bit3       |Bit5|Bit4|
    |----+------------------------------+----+----|
    |  1 | Device code, 1110 is 29s     |  0 |  0 |
    |  2 | Curr. type, meas. variable 1 |  1 |  1 |
    |  3 | Special character 1          |  1 |  1 |
    |  4 | Special character 2          |  1 |  1 |
    |  5 | Measuring range, sign 1      |  1 |  1 |
    -----------------------------------------------

    TM2) Ranges: V AC, V AC+DC, I AC+DC, Ohm, Ohm with buzzer, F, Hz , Temp., dB,
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

    TM3b) Measurement function encoding (also TF)
    -------------------------------------------------
    | Function  | Variable2 | Variable1 |   Index   |
    |-----------+-----------+-----------+-----------|
    |    -      |   0000    |   0000    |      0    |
    |  V DC     |   0000    |   0001    |      1    |
    |  V ACDC   |   0000    |   0010    |      2    |
    |  V AC     |   0000    |   0011    |      3    |
    | mA DC     |   0000    |   0100    |      4    |
    | mA ACDC   |   0000    |   0101    |      5    |
    |  A DC     |   0000    |   0110    |      6    |
    |  A ACDC   |   0000    |   0111    |      7    |
    |-----------+-----------+-----------+-----------|
    |  kOhm     |   0000    |   1000    |      8    |
    |  Farad    |   0000    |   1001    |      9    |
    |  dBV      |   0000    |   1010    |     10    |
    |  Hz UACDC |   0000    |   1011    |     11    |
    |  Hz UAC   |   0000    |   1100    |     12    |
    |  W (mA)   |   0000    |   1101    |     13    |
    |  W (A)    |   0000    |   1110    |     14    |
    |  Diode    |   0000    |   1111    |     15    |
    |-----------+-----------+-----------+-----------|
    | Dio buzz  |   0001    |   0000    |     16    |
    | kOhm buzz |   0001    |   0001    |     17    |
    |  Temp     |   0001    |   0010    |     18    |
    |    -      |   0001    |   0011    |     19    |
    |    -      |   0001    |   0100    |     20    |
    |    -      |   0001    |   0101    |     21    |
    |    -      |   0001    |   0110    |     22    |
    |    -      |   0001    |   0111    |     23    |
    |-----------+-----------+-----------+-----------|
    |    -      |   0001    |   1000    |     24    |
    |    -      |   0001    |   1001    |     25    |
    |    -      |   0001    |   1010    |     26    |
    | mA (W)    |   0001    |   1011    |     27    |
    |  A (W)    |   0001    |   1100    |     28    |
    |  V (W)    |   0001    |   1101    |     29    |
    |  V DC     |   0001    |   1110    |     30    |
    |  V DC     |   0001    |   1111    |     31    |
    -------------------------------------------------

    See also:
    https://www.mikrocontroller.net/attachment/22868/22SM-29S_Interface_Protocol1.pdf
    and
    https://github.com/sigrokproject/libsigrok/blob/master/src/hardware/gmc-mh-1x-2x/protocol.c
    '''

    #######################
    # the class variables #
    #######################

    VERSION = VERSION           # module version
    METRAHIT28S = 0x0C
    METRAHIT29S = 0x0E

    _known_devices = [ 0x0E ]   # METRAHit 29s, add other similar devices, e.g. 0x0C for 28s
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

    _units = ['', 'V_DC', 'V_ACDC', 'V_AC',             # 0x00 .. 0x03
        'mA_DC', 'mA_ACDC', 'A_DC', 'A_ACDC',           # 0x04 .. 0x07
        'kOhm', 'nF', 'dBV', 'Hz',                      # 0x08 .. 0x0B
        'Hz', 'W', 'W', 'V_diode',                      # 0x0C .. 0x0F
        'V_diode_buzzer', 'kOhm_buzzer', '°C', '0x13',  # 0x10 .. 0x13
        '0x14', '0x15', 'Pulse_Wh', 'V_TRMS',           # 0x14 .. 0x17
        'Counter', 'Events_Uacdc', 'Events_Uac', 'mA',  # 0x18 .. 0x1B
        'A', 'V', '0x1E', '0x1F',                       # 0x1C .. 0x1F
    ]

    CMD_FW_STATUS = 3
    CMD_MODE = 6
    CMD_FUNCTION = 7
    CMD_MEASURE = 8

    MODE_NORMAL = 0
    MODE_SEND = 1
    MODE_OFF = 5
    MODE_RESET = 6



    #######################
    # the class interface #
    #######################

    def __init__( self, serial_device = '/dev/ttyUSB0', timeout = 10, known_devices = [ METRAHIT28S, METRAHIT29S ] ):
        'Init internal data, e.g. the name of serial device'
        self._serial_device = serial_device
        self._known_devices = known_devices
        self._timeout = timeout


    def __del__( self ):
        'Close the device when last instance is deleted'
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
            # do not use bytesize=6, use 8 bit and mask received values with 0x3F
            # PL2303 supports 5,6,7,8 bit, ft232 supports only 7 or 8 bit
            self._BD232 = serial.Serial( self._serial_device, baudrate = 9600, timeout = timeout, exclusive=True )
        except:
            return None
        else:
            self.wakeup()
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
        'Set timeout for serial communication'
        self._BD232.timeout = timeout


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


    def get_function( self, index ):
        'Return the measurement function according table TM3b and TF'
        if index < len( self._units ):
            return self._units[ index ]
        else:
            return ''


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


    def send_command( self, cmd, p0=0, p1=0x3F, p2=0x3F, p3=0x3F, p4=0x3F, p5=0x3F, p6=0x3F, p7=0x3F, p8=0x3F ):
        '''Send a command to the meter using the format described in:
        Interface protocol: Bidirectional communication PC - multimeter'''
        time.sleep( .25 )
        self.flush_input()
        data = bytearray()
        # set up the 13 bytes for sending
        addr = 0 # addr can be 1..15, 0: all devices
        data.append( addr<<2 | 0x03 )
        data.append( 0x2b ) # '+'
        data.append( 0x3f ) # '?'
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
        # calculate the checksum
        data.append( self._chksum_13( data ) )
        data = self._encode_14_to_42( data )
        self._BD232.write( data )


    def set_mode( self, mode ):
        '''Set the measurement mode, e.g. "Normal", "Send", "On", "Off", "Reset"
        In case of switching into send mode the multimeter does not send any response.'''
        self.send_command( self.CMD_MODE, mode, mode )


    def set_rate( self, rate_index=4 ):
        '''Set measurement rate between 50 ms and 10 minutes'''
        rates = [ .05, .1, .2, .5, 1, 2, 5, 10, # 0..7
                20, 30, 60, 120, 300, 600       # 0..13
        ]
        if rate_index >= len( rates ): # invalid, set default 1 second
            rate_index = 4
        self.send_command( 4, 2, rate_index + 5 )
        rate = rates[ rate_index ]
        if rate_index > 6: # > 5 s
            self._BD232.timeout = 2 * rate
        return rate


    def set_function( self, MF, RA=0, RA2=0, RA3=0, AR=0, AREC=0 ):
        '''Set the measurement function, according table TF1'''
        self.send_command( self.CMD_FUNCTION, 0, 0, 0, MF, RA, RA2, RA3, AR, AREC )


    def get_cmd_response( self ):
        'Return a bytearray(14) with received 6-bit values inclusive checksum'
        response = bytearray()
        for n in range( 14 ):
            response.append( self._get_byte() )
        return response


    def decode_rsp( self, rsp, outfile=sys.stdout ):
        '''Decode the received response after sending a command'''
        err_msg = [ 'err_0', 'command not used', 'incorrect checksum', 'incorrect block length', 'wrong header', 'parameter out of range'  ]
        adr = rsp[ 0 ]
        if 0 == rsp[ 1 ] & 0x0F: # error
            error = rsp[ 2 ]
            if error in range( len( err_msg ) ):
                error = err_msg[ error ]
            print( 'Request error:', error, file=sys.stderr )
        elif 0x27 != rsp[1] or 0x3F != rsp[2]:
            print( 'Response error:', hex( rsp[1] ), hex( rsp[2] ), file=sys.stderr )
        elif rsp[13] != self._chksum_13( rsp ):
            print( 'Checksum error:', hex( rsp[13] ), hex( self._chksum_13( rsp ) ), file=sys.stderr )
        elif 1 == rsp[3]: # Read first free and occupied address - unimplemented
            if self._decode_rsp_1( rsp, outfile ):
                return
        elif 2 == rsp[3]: # Clear all RAM in multimeter - unimplemented
            if self._decode_rsp_2( rsp, outfile ):
                return
        elif 3 == rsp[3]: # Read firmware version and status
            if self._decode_rsp_3( rsp, outfile ):
                return
        elif 4 == rsp[3]: # Set real time, date, sample rate, trigger, ...
            if self._decode_rsp_4_5( rsp, outfile ):
                return
        elif 5 == rsp[3]: # Read real time, date, sample rate, trigger...
            if self._decode_rsp_4_5( rsp, outfile ):
                return
        elif 6 == rsp[3]: # Set modes or power off
            if self._decode_rsp_6( rsp, outfile ):
                return
        elif 7 == rsp[3]: # Set measurement function, range, autom/man.
            if self._decode_rsp_7( rsp, outfile ):
                return
        elif 8 == rsp[3]: # Get one measurement value
            if self._decode_rsp_8( rsp, outfile ):
                return
        n = 0
        print( 'Response:')
        for b in rsp:
            print('{0:2d}: 0x{1:02x} {2:2d}'.format(n, b, b))
            n += 1


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
            if self._verbose > 2:
                print( 'SLOW:', self._ctmv, hex(self._special), self._dp, self._sign, self._rate )
        elif self._verbose > 2:
            print( 'FAST:', self._ctmv, hex(self._special), self._dp, self._sign )

        if self._verbose > 3:
            print( 'DIGITS:', self._digits )

        self.decode_unit()
        self._adjust_dp()
        self._format_number()
        return self._value


    def _start_detected( self ):
        'Check for start condition 0x0E or 0x1x'
        self._start = self._get_byte()
        self._unexpected_start = False
        return ( self._start in self._known_devices ) or ( self._start & 0x30 == 0x10 )


    def _get_byte( self ):
        'Wait for next byte (2 MSB = 0) with timeout'
        try:
            byte = self._BD232.read()
            if not len( byte ):
                sys.stderr.write( 'Timeout (Enable transfer: hold down "DATA/CLEAR" while switching on)\n' )
                sys.exit()
            byte = ord( byte ) & 0x3F
            if self._verbose > 4:
                print( '_get_byte', hex( byte ) )
            return byte
        except Exception as e:
            print( 'Error:', e, file=sys.stderr )
            sys.exit()

    def _get_digit( self ):
        'Get one digit (4 MSB = 0)'
        byte = self._get_byte()
        if byte < 0x30:
            self._unexpected_start = True
        return byte & 0x0F


    def _adjust_dp( self ):
        '''Reported decimal point position must be corrected for some ranges,'''
        '''in fast mode these values are not correct up to 500 ms after start'''
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
        'Prepare range and sign string'
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


    def _chksum_13( self, data ):
        'Return checksum of data (13 bytes)'
        chs = 0
        for n in range( 13 ):
            b = data[ n ]
            chs -= b
        chs &= 0x3F
        return chs


    def _encode_14_to_42( self, data ):
        'Encode 14 data bytes to 42 transfer bytes, each data byte is sent as three serial bytes'
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


    def _decode_rsp_1( self, rsp, outfile=sys.stdout ):
        'Read first free and occupied address - unimplemented'
        return False


    def _decode_rsp_2( self, rsp, outfile=sys.stdout ):
        'Clear all RAM in multimeter - unimplemented'
        return False


    def _decode_rsp_3( self, rsp, outfile=sys.stdout ):
        '''Decode the received data from command 3
        (Read version A.B of multimeter firmware, status of the multimeter)
        response to cmd3:
        4=fwmin, 5:fwmax, 6:switchpos, 7:fkt,
        8:range, 9:rangeU (in P mode), 10:rangeI (in P mode),
        11:ubat*10, 12:model, 13:chksum'''
        functions = [ '', 'AUTO', 'V_AC', 'V_ACDC', 'V_DC', 'Ohm', 'Diode', '°C', 'F', 'mA', 'A' ]
        print( 'Firmware : ', rsp[5], '.', rsp[4], sep='', file=outfile )
        model = rsp[12]
        switch = rsp[6]
        if switch < len( functions ):
            function = functions[ switch ]
        else:
            function = switch
        if self.METRAHIT29S == model:
            model = 'METRAHit 29S'
        elif self.METRAHIT28S == model:
            model = 'METRAHit 28S'
        print( 'Model    :', model, file=outfile )
        print( 'Switch   :',function , file=outfile )
        print( 'Battery  :', round( rsp[11] * 0.1, 1 ) , 'V', file=outfile )
        return True


    def _decode_rsp_4_5( self, rsp, outfile=sys.stdout ):
        'Set/Read real time, date, sample rate, trigger...'
        if rsp[ 4 ] == 0: # get real time
            hour = 10 * rsp[ 12 ] + rsp[ 11 ]
            minute = 10 * rsp[ 10 ] + rsp[ 9 ]
            second = 10 * rsp[ 8 ] + rsp[ 7 ]
            millis = int( 1000 * ( rsp[6] / 16 + rsp[5] / 256 ) )
            print( '{0:02d}:{1:02d}:{2:02d}.{3:03d}'.format( hour, minute, second, millis ) )
            return True
        elif rsp[ 4 ] == 1: # get real date
            year = 10 * rsp[ 12 ] + rsp[ 11 ]
            if year < 90:
                year += 2000
            else:
                year += 1900
            month = 10 * rsp[ 10 ] + rsp[ 9 ] + 1
            day = 10 * rsp[ 8 ] + rsp[ 7 ] + 1
            print( '{0:4d}-{1:02d}-{2:2d}'.format( year, month, day ) )
            return True
        else: # uninplemented
            # rsp[ 4 ] = 2: Sample rate, filter, ALL Store, duration, resolution, phase ...
            # rsp[ 4 ] = 3: Capture real time, read captured real time
            # rsp[ 4 ] = 4, 5, 7, 8, 9: Trigger
            # rsp[ 4 ] = 10: Duration
            # rsp[ 4 ] = 11: Temperature unit, sensor, temp.ref.value
            # rsp[ 4 ] = 12: Clip transformer value
            # rsp[ 4 ] = 13: Reference value dB
            # rsp[ 4 ] = 14: Internal memory - debug function only
            # rsp[ 4 ] = 15: Read integer time for max.demand measurement
            # rsp[ 4 ] = 18: Command Set Generator
            return False


    def _decode_rsp_6( self, rsp, outfile=sys.stdout ):
        '''Decode the response for "set mode" (normal, send, off, ...)'''
        return False


    def _decode_rsp_7( self, rsp, outfile=sys.stdout ):
        '''Decode the response from command "set measuring function"'''
        function = self.get_function( rsp[7] )
        if function != '':
            print( 'Measurement function:', function )
            return True
        return False


    def _decode_rsp_8( self, rsp, outfile=sys.stdout ):
        '''Decode the received data from command 8
        (Command for getting one measured value from the multimeter)
        response to cmd8: 5:fkt, 6:status, 7..12 digits, 13:chksum'''
        value = 0
        mul = 1
        for b in rsp[7:13]:
            print( b, file=outfile )
            value += b * mul
            mul *= 10
        print( 'Value:', value, file=outfile )
        function = rsp[5]
        print( 'Function:', self.decode_unit( function ), file=outfile )
        print( 'Range:', rsp[6] & 0x0F, (rsp[6] & 0x10) >> 4, file=outfile )
        return True




########################################################
# minimal class invocation example with error handling #
########################################################

if __name__ == "__main__":
    with OpenMetra() as mh:                     # open connection
        if mh is None:                          # check
            print( 'Connect error', file=sys.stderr)
            sys.exit()
        while True:                             # run forever, stop with ^C
            try:
                print( mh.get_measurement() )   # print numeric value
            except KeyboardInterrupt:           # ^C pressed, stop measurement
                print()
                break                           # exit
