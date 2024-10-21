from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Initialize I2C with the common pins for Raspberry Pi Pico
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

# Init oled screen
oled = SSD1306_I2C(128, 64, i2c)

# Initialize buttons
button_up = Pin(9, Pin.IN, Pin.PULL_UP)    	# SW0
button_clear = Pin(8, Pin.IN, Pin.PULL_UP)  # SW1
button_down = Pin(7, Pin.IN, Pin.PULL_UP)   # SW2

# Screen dimensions
WIDTH = 128  # OLED width
HEIGHT = 64  # OLED height

# Initial position
x = 0
y = HEIGHT // 2  # Start from middle height

def clear_screen():
    oled.fill(0)  # Fill with black
    oled.show()

# Clear screen at start
clear_screen()

# Main loop
while True:
    # Draw pixel at current position
    oled.pixel(x, y, 1)  # 1 for white pixel
    oled.show()
    
    # Move x position
    x += 1
    # Check if x value is greater or equal to display max width size
    if x >= WIDTH:
        x = 0  # Wrap around to left side
    
    # Check buttons for vertical movement
    if not button_up.value():  # SW0 pressed
        y = max(0, y - 1)  # Move up, but don't go above screen
    
    if not button_down.value():  # SW2 pressed
        y = min(HEIGHT - 1, y + 1)  # Move down, but don't go below screen
    
    if not button_clear.value():  # SW1 pressed
        clear_screen()
        x = 0 # Reset  x value to 0 (leftmost side of oled display)
        y = HEIGHT // 2  # Reset to middle height
    
    time.sleep(0.01)  # Control drawing speed