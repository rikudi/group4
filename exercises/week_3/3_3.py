''' 
[Exercise 3.3: Display data from a file on the OLED display]

128 pixels drawn on screen. Each pixel represents a value from the data file.
The data file used is capture_250hz_01.txt.
Scroll through the data using the rotary encoder.

Min-max values are displayed at the top of the screen.
Value of the current data point is displayed on the left side of the screen.
 '''

from machine import Pin, I2C
import time
from fifo import Fifo
from filefifo import Filefifo
from ssd1306 import SSD1306_I2C

# Initialize I2C and OLED
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(128, 64, i2c)

# Initialize rotary encoder pins
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)

# Create FIFOs
encoder_fifo = Fifo(32)
data_list = []

'''FILE TO READ'''
filename = 'capture_250Hz_01.txt'
print(f"Reading {filename}...")
try:
    file_fifo = Filefifo(32, name=filename, repeat=False)
    for _ in range(1000):  # Read 1000 values from data file
        value = file_fifo.get()
        data_list.append(float(value))
    print("Successfully read 1000 values")
except Exception as e:
    print(f"Error: {e}")
    exit()

# min and max values
min_value = min(data_list)
max_value = max(data_list)

# Global variables
current_index = 0
WINDOW_SIZE = 128  # Show 128 values at once

def encoder_turn_callback(pin):
    """Interrupt handler for rotary encoder turns"""
    try:
        if rota.value() == rotb.value():
            encoder_fifo.put(0)  # Right
        else:
            encoder_fifo.put(1)  # Left
    except RuntimeError:
        pass

# Attach interrupt
rota.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_callback)

def display_data():
    # Clear display
    oled.fill(0)
    
    # Show min-max range information at the top
    oled.text(f"[{int(min_value)}-{int(max_value)}]", 12, 0)
    
    # Leave room for the header
    header_height = 10
    
    # Calculate y-scale for the display
    y_scale = 54.0 / (max_value - min_value)
    
    # Draw the values
    for i in range(WINDOW_SIZE):
        if current_index + i >= len(data_list):
            break
            
        value = data_list[current_index + i]
        y_pos = int(54 - ((value - min_value) * y_scale)) + header_height
        
        # Draw main data point
        oled.pixel(i, y_pos, 1)
        
        # Draw vertical indicator line at current value (position 0)
        if i == 0:
            # Draw vertical dotted line
            for y in range(header_height, 54 + header_height, 2):  # From y=header_height to y=54 + header_height, skipping every other pixel
                oled.pixel(0, y, 1)
            
            # Highlight the current value point
            if y_pos > header_height and y_pos < 64:
                oled.pixel(0, y_pos-1, 1)
                oled.pixel(0, y_pos+1, 1)
            
            # Draw the current value text aligned with the index pixel
            text_y_pos = max(header_height, min(y_pos, 64 - 10))  # Ensure the text stays within the display height
            oled.text(str(int(value)), 0, text_y_pos, 1)
    
    oled.show()


display_data()


while True:
    if not encoder_fifo.empty():
        event = encoder_fifo.get()
        
        if event == 0:  # Left turn
            if current_index > 0:
                current_index -= 1
                display_data()
                
        elif event == 1:  # Right turn
            if current_index < len(data_list) - WINDOW_SIZE:
                current_index += 1
                display_data()
    
    time.sleep(0.01)