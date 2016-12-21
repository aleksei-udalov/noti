# noti
A daemon for SSD1305 OLED display. Shows battery, time/date, cpu and memory load, weather. For x86 PC.

You need python3 and setup https://github.com/adafruit/Adafruit_Python_SSD1306 and smbus-cffi package.

You can connect SSD1305 to any i2c line on motherboard.
There at least two: on VGA and on SPD RAM.
Connect to VGA is more safe then to RAM, but some motherboards doesnot give i2c clock when no monitor connected.
Connect to RAM 100% works, but its complicated because there is very small lines.

In general, dont do it if you cannot hold the soldering iron.
