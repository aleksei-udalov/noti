from Adafruit_SSD1306 import SSD1306_128_64
import smbus

class dummy:
    def setup(self, *args):
        pass

class customi2c:
    def __init__(self, bus, addr):
        self.bus = smbus.SMBus(bus)
        self.addr = addr

    def write8(self, c, v):
        self.bus.write_byte_data(self.addr, c, v)

    def get_i2c_device(self, x):
        return self

    def writeList(self, reg, data):
        for b in data:
            self.write8(reg, b)


class x86SSD1306(SSD1306_128_64):
    def __init__(self, addr=0x3C, bus=0):
        return super().__init__(rst=None, gpio=dummy(), i2c=customi2c(bus, addr))
    
    def reset(self):
        pass

