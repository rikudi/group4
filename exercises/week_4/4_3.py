from machine import Pin, I2C, Timer
import time
from fifo import Fifo
from filefifo import Filefifo
from ssd1306 import SSD1306_I2C

# Initialize hardware
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(128, 64, i2c)
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)
sw1 = Pin(8, Pin.IN, Pin.PULL_UP)
sw2 = Pin(7, Pin.IN, Pin.PULL_UP)
sw0 = Pin(9, Pin.IN, Pin.PULL_UP)

# Global variables
encoder_fifo = Fifo(32)
data_list = []
current_index = 0
WINDOW_SIZE = 128
scaling = 1.0
offset = 0.0

def read_data():
    global data_list
    filename = 'capture_250hz_01.txt'
    print(f"Reading {filename}...")
    try:
        file_fifo = Filefifo(32, name=filename, repeat=False)
        raw_data = [float(file_fifo.get()) for _ in range(1800)]
        data_list = [sum(raw_data[i:i+5]) / 5 for i in range(0, 1800, 5)]
        print("Successfully read and processed 1800 values")
    except Exception as e:
        print(f"Error: {e}")
        data_list = []

def encoder_turn_callback(pin):
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
    oled.fill(0)
    
    if not data_list:
        oled.text("Press SW1", 0, 0)
        oled.show()
        return

    # Get visible data window
    visible_data = data_list[current_index:current_index + WINDOW_SIZE]
    
    # Calculate min/max before offset
    min_val = min(visible_data)
    max_val = max(visible_data)
    
    # Use full display height
    display_height = 64
    
    # Calculate y-scale with scaling factor
    if max_val != min_val:
        y_scale = (display_height * scaling) / (max_val - min_val)
    else:
        y_scale = 1
    
    # Draw data points
    for i, value in enumerate(visible_data):
        if i >= WINDOW_SIZE:
            break
            
        # Calculate base y position with scaling
        y_pos = int(display_height - ((value - min_val) * y_scale))
        # Apply offset for vertical positioning
        y_pos = y_pos - int(offset)
        # Clamp to display bounds
        y_pos = min(display_height - 1, max(0, y_pos))
        
        # Draw pixel
        oled.pixel(i, y_pos, 1)
    
    # Show scale and offset info
    oled.text(f"x{scaling:.1f} o:{int(offset)}", 0, 0, 1)
    
    oled.show()

def check_inputs(timer):
    global current_index, scaling, offset
    
    try:
        if sw1.value() == 0:
            read_data()
            display_data()
            time.sleep(0.2)  # Shorter debounce
        
        if not encoder_fifo.empty():
            event = encoder_fifo.get()
            
            if event == 0:  # Left turn
                if sw2.value() == 0:
                    scaling *= 1.1
                elif sw0.value() == 0:
                    offset += 1
                elif current_index > 0:
                    current_index -= 1
                display_data()
            elif event == 1:  # Right turn
                if sw2.value() == 0:
                    scaling /= 1.1
                elif sw0.value() == 0:
                    offset -= 1
                elif current_index < len(data_list) - WINDOW_SIZE:
                    current_index += 1
                display_data()
    
    except Exception as e:
        print(f"Error: {e}")

def init_display():
    try:
        # Initialize I2C with error handling
        i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)  # Added frequency specification
        
        # Scan for I2C devices
        devices = i2c.scan()
        if not devices:
            raise Exception("No I2C devices found")
            
        # Initialize OLED with small delay
        oled = SSD1306_I2C(128, 64, i2c)
        time.sleep(0.1)  # Allow display to initialize
        
        return oled
    except Exception as e:
        print(f"Display initialization error: {e}")
        return None

def main():
    global oled
    
    # Initialize display with retry
    retry_count = 3
    while retry_count > 0:
        oled = init_display()
        if oled:
            break
        print(f"Retrying display initialization... ({retry_count} attempts left)")
        time.sleep(1)
        retry_count -= 1
    
    if not oled:
        print("Failed to initialize display")
        return
    
    try:
        # Initialize display
        oled.fill(0)
        oled.text("Press SW1", 0, 0)
        oled.show()
        time.sleep(0.1)  # Small delay after display operation
        
        # Setup timer for periodic checks
        timer = Timer()
        timer.init(freq=100, mode=Timer.PERIODIC, callback=check_inputs)
        
    except Exception as e:
        print(f"Main initialization error: {e}")

if __name__ == "__main__":
    main()