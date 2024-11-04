from machine import Pin, I2C, time_pulse_us
import time
from fifo import Fifo
from ssd1306 import SSD1306_I2C  # OLED display driver

# Initialize I2C and OLED
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(128, 64, i2c)  # 128x64 OLED display

# Initialize LEDs - Käytetään Picon GPIO-pinnien oikeita numeroita
led1 = Pin(22, Pin.OUT, value=0)  # LED1, alustetaan pois päältä
led2 = Pin(21, Pin.OUT, value=0)  # LED2, alustetaan pois päältä
led3 = Pin(20, Pin.OUT, value=0)  # LED3, alustetaan pois päältä

# Initialize rotary encoder pins
rota = Pin(10, Pin.IN, Pin.PULL_UP)  # ROTA
rotb = Pin(11, Pin.IN, Pin.PULL_UP)  # ROTB
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)  # Encoder button

# Create FIFO for encoder events
fifo = Fifo(32)

# Variables for button debouncing
last_button_time = 0
DEBOUNCE_MS = 500  # 500ms debounce time

# Interrupt handler for rotary encoder turns
def encoder_turn_callback(pin):
    try:
        if rota.value() == rotb.value():  # Check direction
            fifo.put(1)  # Right turn
        else:
            fifo.put(0)  # Left turn
    except RuntimeError:
        pass  # Ignore if FIFO is full

# Interrupt handler for button press
def button_callback(pin):
    global last_button_time
    current_time = time.ticks_ms()
    
    # Check if enough time has passed since last press
    if time.ticks_diff(current_time, last_button_time) > DEBOUNCE_MS:
        try:
            fifo.put(2)  # Button press event
            last_button_time = current_time
        except RuntimeError:
            pass  # Ignore if FIFO is full

# Attach interrupts
rota.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_callback)
rot_push.irq(trigger=Pin.IRQ_FALLING, handler=button_callback)

# Menu state variables
menu_items = ["LED1", "LED2", "LED3"]
current_selection = 0
led_states = [False, False, False]  # Track LED states
leds = [led1, led2, led3]  # LED pin objects

def toggle_led(led_index):
    """Toggle LED state and update the actual LED"""
    led_states[led_index] = not led_states[led_index]
    if led_states[led_index]:
        leds[led_index].on()  # Explicitly turn LED
    else:
        leds[led_index].off()  # Explicitly turn LED off

def display_menu():
    oled.fill(0)  # Clear display
    
    # Display title
    oled.text("LED Menu:", 0, 0)
    
    # Display menu items
    for i, item in enumerate(menu_items):
        y_pos = (i + 1) * 16  # Space items vertically
        # Show selection arrow
        if i == current_selection:
            oled.fill_rect(0, y_pos, 128, 12, 1)  # Highlight selected row
            oled.text(item, 10, y_pos + 2, 0)  # White text on black background
        else:
            oled.text(item, 10, y_pos + 2)  # Normal text
            
        # Show LED state
        state = "ON" if led_states[i] else "OFF"
        if i == current_selection:
            oled.text(state, 80, y_pos + 2, 0)  # White text on black for selected
        else:
            oled.text(state, 80, y_pos + 2)  # Normal text
    
    oled.show()  # Update display

# Initial menu display
display_menu()

# Main loop
while True:
    if not fifo.empty():
        event = fifo.get()
        
        if event == 0:  # Left turn
            current_selection = (current_selection - 1) % len(menu_items)
            display_menu()
            
        elif event == 1:  # Right turn
            current_selection = (current_selection + 1) % len(menu_items)
            display_menu()
            
        elif event == 2:  # Button press
            toggle_led(current_selection)  # Use new toggle function
            display_menu()
    
    # Small delay to avoid busy waiting
    time.sleep(0.01)