#!/usr/bin/python3

from x86SSD1306 import x86SSD1306
from PIL import Image, ImageFont, ImageDraw
from time import sleep
import datetime
import subprocess
import math
import psutil
import requests
import json
import calendar

weather_enabled = True
try:
    from weather_key import WEATHER_KEY
except:
    weather_enabled = False
    print('weather disabled, go to http://openweathermap.org and get API key')
COMMAND_MODPROBE = 'modprobe i2c-dev'
COMMAND_BAT_LEVEL = 'cat /sys/class/power_supply/BAT0/capacity'
BAT_WARN_LEVEL = 50
COMMAND_AC_ONLINE = 'cat /sys/class/power_supply/AC/online'
BAT_POS = (1, 40)
BAT_SIZE = (50, 6)
CLOCK_POS = (1, 0)
BAT_WARN_POS = (44, 28)
CPU_POS = (1, 12)
CPU_SIZE = (127, 16)
MEM_POS = (1, 30)
MEM_SIZE = (125, 6)
COMMAND_GET_TEMP = 'cat /sys/class/thermal/thermal_zone0/temp'
CPU_TEMP_POS = (64, 38)
ABSOLUTE_ZERO = 273.15
WEATHER_CITY = 'Saratov'
WEATHER_COUNTRY = 'ru'
CITY_POS = (80, 37)
WEATHER_POS = (1, 50)

def percent_rectangle(r, percent):
    r[2] = r[0] + (r[2] - r[0]) * percent // 100

def get_rectangle(POS, SIZE):
    return [POS[0], POS[1], SIZE[0] + POS[0], SIZE[1] + POS[1]]

def get_bat_level():
    try:
        return int(subprocess.getoutput(COMMAND_BAT_LEVEL))
    except:
        return None

def is_ac_online():
    return int(subprocess.getoutput(COMMAND_AC_ONLINE))

def draw_cpu_template(draw):
    for r in cpu_rectangles:
        draw.rectangle(r, outline=255)

def make_template():
    template = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(template)
    draw.rectangle(get_rectangle(BAT_POS, BAT_SIZE), outline=255)
    draw_cpu_template(draw)
    draw.rectangle(get_rectangle(MEM_POS, MEM_SIZE), outline=255)
    return template

def render_bat(draw):
    r = get_rectangle(BAT_POS, BAT_SIZE)
    bat_level = get_bat_level()
    if bat_level is not None:
        percent_rectangle(r, get_bat_level())
        draw.rectangle(r, fill=255)
    else:
        draw.rectangle(r, fill=0)
        draw.text((BAT_POS[0], BAT_POS[1] - 2), '   ???', fill=255)
    if is_ac_online():
        draw.text((BAT_POS[0] + BAT_SIZE[0] + 2, BAT_POS[1] - 2), '+', fill=255)

def render_clock(draw):
    t = datetime.datetime.time(datetime.datetime.now())
    d = datetime.date.today() #.date(datetime.datetime.now())
    day = str(d.day)
    month = str(d.month)
    weekday = calendar.day_name[d.weekday()]
    draw.text(CLOCK_POS, t.isoformat()[:5]+' '+day+'.'+month+' '+weekday,  fill=255)

def render_cpu(draw):
    for r, percent in zip(cpu_rectangles, psutil.cpu_percent(percpu=True)):
        r = r[:]
        percent_rectangle(r, percent)
        draw.rectangle(r, fill=255)

def render_mem(draw):
    r = get_rectangle(MEM_POS, MEM_SIZE)
    percent_rectangle(r, psutil.virtual_memory().percent)
    draw.rectangle(r, fill=255)

def get_cpu_temp():
    return int(subprocess.getoutput(COMMAND_GET_TEMP)) // 1000

def render_temp(draw):
    draw.text(CPU_TEMP_POS, 'CPU: ' + str(get_cpu_temp())+' C', fill=255)

def render_weather(draw):
    if not weather_enabled:
        return
    if weather is None:
        draw.text(WEATHER_POS, 'no weather data', fill=255)
        return
    temp = weather['main']['temp'] - ABSOLUTE_ZERO
    temp = round(temp, 1)
    if temp > 0:
        temp = '+' + str(temp)
    else:
        temp = str(temp)
    desc = weather['weather'][0]['description']
    draw.text(WEATHER_POS, temp + ' C ' + desc, fill=255)

def render(template):
    image = template.copy()
    draw = ImageDraw.Draw(image)
    render_bat(draw)
    render_clock(draw)
    render_cpu(draw)
    render_mem(draw)
    render_temp(draw)
    render_weather(draw)
    return image

def show_bat_warning():
    image = Image.new('1', (128, 64), 0)
    draw = ImageDraw.Draw(image)
    for x in range(1, 6):
        draw.rectangle((0, 0, 128, 64), fill=(255 if x%2 else 0))
        draw.text(BAT_WARN_POS, 'POWER', fill=(0 if x%2 else 255))
        disp.image(image)
        disp.display()

def get_weather():
    if not weather_enabled:
        return
    try:
        return json.loads(requests.get('http://api.openweathermap.org/data/2.5/weather?q=' + WEATHER_CITY + ',' + WEATHER_COUNTRY + '&Appid=' + WEATHER_KEY).content.decode('UTF-8'))
    except:
        return None
        
def find_bus():
    for i in (0, 9) + tuple(range(1, 9)):
        print('checking bus %i' % i)
        if subprocess.getoutput('i2cdetect -y %i | grep 3c > /dev/null ; echo $?' % i) == '0':
            print('device found')
            return i
    raise Exception('cannot found device')
        
subprocess.getoutput(COMMAND_MODPROBE)
disp = x86SSD1306(bus=find_bus())
disp.begin()

cpu_count = len(psutil.cpu_percent(percpu=True))
cpu_rows = 1 if cpu_count < 3 else 2
cpu_cols = math.ceil(cpu_count // cpu_rows)
cpu_rectangle_width = CPU_SIZE[0] / cpu_cols
cpu_rectangle_height = CPU_SIZE[1] / cpu_rows
cpu_rectangles = []
for row in range(cpu_rows):
    for col in range(cpu_cols):
        cpu_rectangles.append([
                CPU_POS[0] + col * cpu_rectangle_width,
                CPU_POS[1] + row * cpu_rectangle_height,
                CPU_POS[0] + (col+1) * cpu_rectangle_width - 2,
                CPU_POS[1] + (row+1) * cpu_rectangle_height - 2,
        ])
        if len(cpu_rectangles) == cpu_count:
            # if odd cpu count
            break

template = make_template()
weather = get_weather()
weather_counter = 0

while True:
    if not is_ac_online() and get_bat_level() < BAT_WARN_LEVEL:
        show_bat_warning()
    image = render(template)
#    image.save('out.jpg')
    try:
        disp.image(image)
        disp.display()
    except:
        pass
    sleep(1.5)
    weather_counter += 1
    if weather is None or weather_counter == 400: # 1 request in 30 minutes
        weather = get_weather()
        weather_counter = 0
