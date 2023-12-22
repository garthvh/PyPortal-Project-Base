import time
import board
import microcontroller
import displayio
import busio
from analogio import AnalogIn
import neopixel
import adafruit_adt7410
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from adafruit_button import Button
import adafruit_touchscreen
from adafruit_pyportal import PyPortal

# Screen Setup 
# Landscape - 0 
# Portrait - 270
rotation = 0
max_chars = 30

# Sounds
soundDemo = "/sounds/sound.wav"
soundBeep = "/sounds/beep.wav"
soundTab = "/sounds/tab.wav"

# Colors
# Standard Colors
GREEN = 0x00FF00
BLUE = 0x0000FF
PURPLE = 0xFF00FF
DARK_PURPLE = 0x2f065e
YELLOW = 0xFFFF00
ORANGE = 0xFF9900
PINK = 0xFF5733
RED = 0xFF0000
WHITE = 0xFFFFFF
GRAY = 0x1A1A1A
BLACK = 0x000000
# Theme Colors
ACCENT = BLUE
TEXT = WHITE
BACKGROUND = 0x2C2D3C
SELECTED_BACKGROUND = 0x5C5B5C
OUTLINE = 0x767676
SELECTED_OUTLINE = 0x2E2E2E

# Default Label padding
TABS_X = 15
TABS_Y = 15

# Default button size:
BUTTON_HEIGHT = 75
BUTTON_WIDTH = 100

# Default State for tabs and the neopixel switch
view_live = 1
switch_state = 0
switch_x = 130
switch_y = 75

# ------------- Functions ------------- #
# Backlight function
# Value between 0 and 1 where 0 is OFF, 0.5 is 50% and 1 is 100% brightness.
def set_backlight(val):
    val = max(0, min(1.0, val))
    try:
        board.DISPLAY.auto_brightness = False
    except AttributeError:
        pass
    board.DISPLAY.brightness = val

# Set visibility of layer
def layerVisibility(state, layer, target):
    try:
        if state == "show":
            time.sleep(0.1)
            layer.append(target)
        elif state == "hide":
            layer.remove(target)
    except ValueError:
        pass

# This will handle switching Images and Icons
def set_image(group, filename):
    """Set the image file for a given goup for display.
    This is most useful for Icons or image slideshows.
        :param group: The chosen group
        :param filename: The filename of the chosen image
    """
    print("Set image to ", filename)
    if group:
        group.pop()

    if not filename:
        return  # we're done, no icon desired

    image = displayio.OnDiskBitmap(filename)
    image_sprite = displayio.TileGrid(image, pixel_shader=image.pixel_shader)

    group.append(image_sprite)

# return a reformatted string with word wrapping using PyPortal.wrap_nicely
def text_box(target, top, string, max_chars):
    text = pyportal.wrap_nicely(string, max_chars)
    new_text = ""
    test = ""

    for w in text:
        new_text += "\n" + w
        test += "M\n"

    text_height = Label(font, text="M", color=0x03AD31)
    text_height.text = test  # Odd things happen without this
    glyph_box = text_height.bounding_box
    target.text = ""  # Odd things happen without this
    # target.y = int(glyph_box[3] / 2) + top
    target.y = int(glyph_box[3] / 2) + top
    target.text = new_text

def get_Temperature(source):
    if source:  # Only if we have the temperature sensor
        celsius = source.temperature
    else:  # No temperature sensor
        celsius = microcontroller.cpu.temperature
    return (celsius * 1.8) + 32

# ------------- Inputs and Outputs Setup ------------- #
light_sensor = AnalogIn(board.LIGHT)
try:
    # attempt to init. the temperature sensor
    i2c_bus = busio.I2C(board.SCL, board.SDA)
    adt = adafruit_adt7410.ADT7410(i2c_bus, address=0x48)
    adt.high_resolution = True
except ValueError:
    # Did not find ADT7410. Probably running on Titano or Pynt
    adt = None

# ------------- Screen Setup ------------- #
pyportal = PyPortal()
# pyportal.set_background("/images/loading.bmp")  # Display an image until the loop starts
pyportal.set_background(PURPLE)
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=1)

# Touchscreen setup  [ Rotate 270 ]
display = board.DISPLAY
display.rotation = rotation

if board.board_id == "pyportal_titano":
    if rotation == 0: 
        screen_width = 480
        screen_height = 320
        max_chars = 50
    else:
        screen_width = 320
        screen_height = 480
        max_chars = 32
    set_backlight(
        1
    )  # 0.3 brightness does not cause the display to be visible on the Titano
else:
    if rotation == 0: 
        screen_width = 320
        screen_height = 240
    else:
        screen_width = 240
        screen_height = 320
    set_backlight(0.3)

# We want three buttons across the top of the screen
TAB_BUTTON_Y = 0
TAB_BUTTON_HEIGHT = 60
TAB_BUTTON_WIDTH = int(screen_width / 2)

# Portrait Touchscreen (rotation - 270)
if rotation == 270:
    ts = adafruit_touchscreen.Touchscreen(
        board.TOUCH_YD,
        board.TOUCH_YU,
        board.TOUCH_XR,
        board.TOUCH_XL,
        calibration=((5200, 59000), (5800, 57000)),
        size=(screen_width, screen_height),
    )
# Landscape Touchscreen (rotation - 0)
elif rotation == 0:
    ts = adafruit_touchscreen.Touchscreen(
        board.TOUCH_XL,
        board.TOUCH_XR,
        board.TOUCH_YD,
        board.TOUCH_YU,
        calibration=((5200, 59000), (5800, 57000)),
        size=(screen_width, screen_height),
    )

# ------------- Display Groups ------------- #
splash = displayio.Group()  # The Main Display Group
view_neopixel = displayio.Group()  # Group for View 1 objects
view_sensors = displayio.Group()  # Group for View 3 objects

# ------------- Setup for Images ------------- #
# bg_group = displayio.Group()
# splash.append(bg_group)
# set_image(bg_group, "/images/BGimage.bmp")

# ---------- Text Boxes ------------- #
# Set the font and preload letters
font_small = bitmap_font.load_font("/fonts/Arial-12.bdf")
font_small.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")
font = bitmap_font.load_font("/fonts/Arial-16.bdf")
font.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")
font_large = bitmap_font.load_font("/fonts/Arial-Bold-24.bdf")
font_large.load_glyphs(b"abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()")

sensors_label = Label(font, text="Data View", color=TEXT)
sensors_label.x = TABS_X
sensors_label.y = TABS_Y
view_sensors.append(sensors_label)

sensor_data = Label(font, text="Data View", color=TEXT)
sensor_data.x = TABS_X * 3  # Indents the text layout
sensor_data.y = 215
if rotation == 270:
    sensor_data.y =265
view_sensors.append(sensor_data)

# ---------- Buttons ------------- #
buttons = []

# Tabs
button_neopixel = Button(
    x=0,  # Start at left
    y=0,  # Start at top
    width=TAB_BUTTON_WIDTH,  # Calculated width
    height=TAB_BUTTON_HEIGHT,  # Static height
    label="Neo Pixel",
    label_font=font,
    label_color=WHITE,
    fill_color=SELECTED_BACKGROUND,
    outline_color=OUTLINE,
    selected_fill=GRAY,
    selected_outline=SELECTED_OUTLINE,
    selected_label=BACKGROUND,
)
buttons.append(button_neopixel)  # adding this button to the buttons group

button_sensors = Button(
    x=TAB_BUTTON_WIDTH * 1,  # Start after width of 2 buttons
    y=0,
    width=TAB_BUTTON_WIDTH,
    height=TAB_BUTTON_HEIGHT,
    label="Sensors",
    label_font=font,
    label_color=WHITE,
    fill_color=SELECTED_BACKGROUND,
    outline_color=OUTLINE,
    selected_fill=GRAY,
    selected_outline=SELECTED_OUTLINE,#0x2E2E2E,
    selected_label=BACKGROUND,
)
buttons.append(button_sensors)  # adding this button to the buttons grou

# Add all of the tabs to the splash Group
for b in buttons:
    splash.append(b)

if rotation == 270:
    switch_x = 50   

# Neopixel switch button
button_switch = Button(
    style=Button.ROUNDRECT,
    x=switch_x,
    y=switch_y,
    width=220,
    height=65,
    name="Light Switch",
    label_font=font_large,
    fill_color=SELECTED_BACKGROUND,
    selected_fill=0x1A1A1A,
)
buttons.append(button_switch)  # adding this button to the buttons group
view_neopixel.append(button_switch)

# Neopixel Color Buttons - view_neopixel
color_btn = [
  
    {'name':'white', 'pos':(10, 155), 'color':WHITE},
    {'name':'yellow', 'pos':(130, 155), 'color':YELLOW},
    {'name':'orange', 'pos':(250, 155), 'color':ORANGE},
    {'name':'green', 'pos':(370, 155), 'color':GREEN},
    {'name':'red', 'pos':(10, 240), 'color':RED},
    {'name':'purple', 'pos':(130, 240), 'color':PURPLE},
    {'name':'blue', 'pos':(250, 240), 'color':BLUE},
    {'name':'dark_purple', 'pos':(370, 240), 'color':DARK_PURPLE}
]

if rotation == 270:
    BUTTON_HEIGHT = 90
    BUTTON_WIDTH = 90
    color_btn = [
        {'name':'white', 'pos':(15, 165), 'color':WHITE},
        {'name':'yellow', 'pos':(115, 165), 'color':YELLOW},
        {'name':'orange', 'pos':(215, 165), 'color':ORANGE},
        {'name':'green', 'pos':(15, 265), 'color':GREEN},
        {'name':'pink', 'pos':(115, 265), 'color':PINK},
        {'name':'red', 'pos':(215, 265), 'color':RED},
        {'name':'purple', 'pos':(15, 365), 'color':PURPLE},
        {'name':'blue', 'pos':(115, 365), 'color':BLUE},
        {'name':'dark_purple', 'pos':(215, 365), 'color':DARK_PURPLE}
    ]
    
# generate color buttons from color_btn list
for i in color_btn:
    button = Button(x=i['pos'][0], y=i['pos'][1],
                    width=BUTTON_WIDTH, height=BUTTON_HEIGHT, name=i['name'],
                    fill_color=i['color'], style=Button.ROUNDRECT)
    buttons.append(button)
    view_neopixel.append(button)

def switch_view(what_view):
    global view_live
    if what_view == 1:
        button_neopixel.selected = False
        button_sensors.selected = True
        layerVisibility("hide", splash, view_sensors)
        layerVisibility("show", splash, view_neopixel)

    elif what_view == 2:
        button_neopixel.selected = True
        button_sensors.selected = False
        layerVisibility("hide", splash, view_neopixel)
        layerVisibility("show", splash, view_sensors)

    # Set global button state
    view_live = what_view
    print("View {view_num:.0f} On".format(view_num=what_view))

# Set veriables and startup states
button_neopixel.selected = False
button_sensors.selected = True
button_switch.label = "OFF"
button_switch.selected = True

layerVisibility("show", splash, view_neopixel)
layerVisibility("hide", splash, view_sensors)

text_box(
    sensors_label,
    TABS_Y,
    "This screen displays readings from the built in sensors on the PyPortal: Touch, Light and Temperature.",
    max_chars,
)

board.DISPLAY.root_group = splash

# ------------- Loop ------------- #
while True:
    # Sensor Data Readings
    touch = ts.touch_point
    light = light_sensor.value
    sensor_data.text = "Touch: {}\nLight: {}\nTemp: {:.0f}°F".format(
        touch, light, get_Temperature(adt)
    )

    # ------------- Handle Button Presses ------------- #
    if touch:  # Only do this if the screen is touched
        # loop with buttons using enumerate() to number each button group as i
        for i, b in enumerate(buttons):
            if b.contains(touch):  # Test each button to see if it was pressed
                print("button{} pressed".format(i))
                if i == 0 and view_live != 1:  # only if view_neopixel is visible
                    pyportal.play_file(soundTab)
                    switch_view(1)
                    while ts.touch_point:
                        pass
                if i == 1 and view_live != 2:  # only if view_sensors is visible
                    pyportal.play_file(soundTab)
                    switch_view(2)
                    while ts.touch_point:
                        pass
                if  i == 2:  # view_neopixel on / off button
                    if view_live == 1:
                        # Toggle switch button type
                        pyportal.play_file(soundBeep)
                        if switch_state == 0:
                            switch_state = 1
                            b.label = "ON"
                            b.selected = False
                            pixel.fill(WHITE)
                            print("Switch ON")
                        else:
                            switch_state = 0
                            b.label = "OFF"
                            b.selected = True
                            pixel.fill(BLACK)
                            print("Switch OFF")
                        # for debounce
                        while ts.touch_point:
                            pass
                        print("Neo Pixel Switch Pressed")
                if i > 2:
                    if view_live == 1:
                        # Momentary color button 
                        b.selected = True
                        print("Color Button Pressed")
                        pyportal.play_file(soundBeep)
                        b.selected = True
                        pixel.fill(b.fill_color)
                        switch_state = 1
                        button_switch.label = "ON"
                        button_switch.selected = False
                        # for debounce
                        while ts.touch_point:
                            pass
                        print("Color Button Released")
                        b.selected = False