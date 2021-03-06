# //*****************************************************************************
# * | File        :	  epd7in5b.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :
# *----------------
# * |	This version:   V3.0
# * | Date        :   2018-11-12
# * | Info        :   python2 demo
# * 1.Remove:
#   digital_write(self, pin, value)
#   digital_read(self, pin)
#   delay_ms(self, delaytime)
#   set_lut(self, lut)
#   self.lut = self.lut_full_update
# * 2.Change:
#   display_frame -> TurnOnDisplay
#   set_memory_area -> SetWindow
#   set_memory_pointer -> SetCursor
#   get_frame_buffer -> getbuffer
#   set_frame_memory -> display
# * 3.How to use
#   epd = epd7in5b.EPD()
#   epd.init(epd.lut_full_update)
#   image = Image.new('1', (epd7in5b.EPD_WIDTH, epd7in5b.EPD_HEIGHT), 255)
#   ...
#   drawing ......
#   ...
#   epd.display(getbuffer(image))
# ******************************************************************************//
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and//or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


import epdconfig
from PIL import Image
import RPi.GPIO as GPIO
import logging

class Epd:
    # Display resolution
    Width                                   = 640
    Height                                  = 384

    # EPD7IN5 commands
    PanelSetting                               = 0x00
    PowerSetting                               = 0x01
    PowerOff                                   = 0x02
    PowerOffSequenceSetting                    = 0x03
    PowerOn                                    = 0x04
    PowerOnMeasure                             = 0x05
    BoosterSoftStart                           = 0x06
    DeepSleep                                  = 0x07
    DataStartTransmission1                     = 0x10
    DataStop                                   = 0x11
    DisplayRefresh                             = 0x12
    ImageProcess                               = 0x13
    LutForVcom                                 = 0x20
    LutBlue                                    = 0x21
    LutWhite                                   = 0x22
    LutGray1                                   = 0x23
    LutGray2                                   = 0x24
    LutRed0                                    = 0x25
    LutRed1                                    = 0x26
    LutRed2                                    = 0x27
    LutRed3                                    = 0x28
    LutXon                                     = 0x29
    PllControl                                 = 0x30
    TemperatureSensorCommand                   = 0x40
    TemperatureCalibration                     = 0x41
    TemperatureSensorWrite                     = 0x42
    TemperatureSensorRead                      = 0x43
    VcomAndDataIntervalSetting                 = 0x50
    LowPowerDetection                          = 0x51
    TconSetting                                = 0x60
    TconResolution                             = 0x61
    SpiFlashControl                            = 0x65
    Revision                                   = 0x70
    GetStatus                                  = 0x71
    AutoMeasurementVcom                        = 0x80
    ReadVcomValue                              = 0x81
    VcmDcSetting                               = 0x82
    
    # LUT Tables
    # VCOM (11 bytes)
    LutC = bytearray([
        
        ])
    # Black (13 bytes)
    LutB = bytearray([
        
        ])
    # White (13 bytes)
    LutW = bytearray([
        
        ])
    # Gray 1 (13 bytes)
    LutG1 = bytearray([
        0x01, 0x00
        ])
    # Gray 2 (13 bytes)
    LutG2 = bytearray([
        
        ])
    # Red 0 (13 bytes)
    LutR0 = bytearray([
        
        ])
    # Red 1 (13 bytes)
    LutR1 = bytearray([
        
        ])
    # Red 2 (13 bytes)
    LutR2 = bytearray([
        
        ])
    # Red 3 (13 bytes)
    LutR3 = bytearray([
        
        ])
    # XON (10 bytes)
    LutX = bytearray([
        
        ])
        
    ColorLookupNamed = { "black": 0b000,
                         "grey1": 0b001,
                         "grey2": 0b010,
                         "white": 0b011,
                         "red0" : 0b100,
                         "red1" : 0b101,
                         "red2" : 0b110,
                         "red3" : 0b111
                         }
    ColorLookupPalette8 = { 0: 0b000,
                            1: 0b001,
                            2: 0b010,
                            3: 0b011,
                            4: 0b100,
                            5: 0b101,
                            6: 0b110,
                            7: 0b111
                            }
    ColorLookupPalette3 = { 0: 0b000,
                            1: 0b011,
                            2: 0b100
                            }
                         
    def __init__(self):
        self.logger = logging.getLogger('eink_status.epd7in5b')
        self.logger.debug('__init__')
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN

    # Hardware reset
    def reset(self):
        # epdconfig.digital_write(self.reset_pin, GPIO.HIGH)
        # epdconfig.delay_ms(200) 
        epdconfig.digital_write(self.reset_pin, GPIO.LOW)         # module reset
        epdconfig.delay_ms(200)
        epdconfig.digital_write(self.reset_pin, GPIO.HIGH)
        epdconfig.delay_ms(200)   

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, GPIO.LOW)
        epdconfig.spi_writebyte([command])

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, GPIO.HIGH)
        epdconfig.spi_writebyte([data])
        
    def wait_until_idle(self):
        self.logger.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: busy, 1: idle
            epdconfig.delay_ms(100)
        self.logger.debug("e-Paper busy release")
            
    def init(self):
        if (epdconfig.module_init() != 0):
            return -1
            
        self.reset()
        
        self.send_command(self.PowerSetting)
        self.send_data(0x37)
        self.send_data(0x00)
        self.send_command(self.PanelSetting)
        self.send_data(0xCF)
        self.send_data(0x08)
        self.send_command(self.BoosterSoftStart)
        self.send_data(0xc7)
        self.send_data(0xcc)
        self.send_data(0x28)
        self.send_command(self.PowerOn)
        self.wait_until_idle()
        self.send_command(self.PllControl)
        self.send_data(0x3c)
        self.send_command(self.TemperatureCalibration)
        self.send_data(0x00)
        self.send_command(self.VcomAndDataIntervalSetting)
        self.send_data(0x77)
        self.send_command(self.TconSetting)
        self.send_data(0x22)
        self.send_command(self.TconResolution)
        self.send_data(0x02)     #source 640
        self.send_data(0x80)
        self.send_data(0x01)     #gate 384
        self.send_data(0x80)
        self.send_command(self.VcmDcSetting)
        self.send_data(0x1E)      #decide by LUT file
        self.send_command(0xe5)           #FLASH MODE
        self.send_data(0x03)

        return 0

    def pxmap(self, pixel):
        pixel = pixel % 3
        return self.pxmap3(pixel)

    def pxmap3(self, pixel):
        return self.ColorLookupPalette3[pixel]

    def pxmap8(self, pixel):
        return self.ColorLookupPalette8[pixel]

    def SetLUTG2(self):
        self.send_command(self.LutGray1)
        for i in range(0, 19):
            for byte in self.LutG1:
                send_data(byte)
        
    def Display(self, image):
        self.send_command(self.DataStartTransmission1)
        imagedata = iter(list(image.getdata()))
        for pixel in imagedata:
            byte = self.pxmap(pixel)
            byte = byte << 4
            pixel = next(imagedata, 0)
            byte = byte | self.pxmap(pixel)
            self.send_data(byte)

        self.send_command(self.DisplayRefresh)
        epdconfig.delay_ms(100)
        self.wait_until_idle()

    def Clear(self, color="white"):
        self.send_command(self.DataStartTransmission1)
        byte = self.ColorLookupNamed[color]
        byte = byte << 4
        byte = byte | self.ColorLookupNamed[color]
        for i in range(0, self.Width // 8 * self.Height):
            self.send_data(byte)
            self.send_data(byte)
            self.send_data(byte)
            self.send_data(byte)
        self.send_command(self.DisplayRefresh)
        epdconfig.delay_ms(100)
        self.wait_until_idle()

    def sleep(self):
        self.send_command(self.PowerOff)
        self.wait_until_idle()
        self.send_command(self.DeepSleep)
        self.send_data(0xA5)

