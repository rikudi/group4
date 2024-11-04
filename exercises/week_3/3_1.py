from machine import Pin, PWM
import time
from fifo import Fifo  # Import the Fifo class

# Initialize LED on GP22 (D1)
led = PWM(Pin(22))  # D1
led.freq(1000)  # Set PWM frequency for smooth brightness control

# Initialize rotary encoder pins
rota = Pin(10, Pin.IN, Pin.PULL_UP)  # ROTA
rotb = Pin(11, Pin.IN, Pin.PULL_UP)  # ROTB
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)  # Encoder button (ROT_PUSH)

# LED state and brightness level
led_on = False  # Start with LED off
brightness = 0  # Initial brightness (0 to 65535 for PWM)

# Create a FIFO instance for encoder turn events
fifo = Fifo(32)  # Create FIFO with size 32 bytes

# Interrupt handler for rotary encoder turns
def encoder_callback(pin):
    try:
        if rota.value() == rotb.value():  # Check direction
            fifo.put(1)  # Turned right
        else:
            fifo.put(0)  # Turned left
    except RuntimeError:
        # If FIFO is full, silently ignore the overflow
        pass

# Attach interrupt to the encoder's A pin
rota.irq(trigger=Pin.IRQ_RISING, handler=encoder_callback)

# Function to debounce the encoder button press
def debounce(pin):
    time.sleep(0.05)
    return pin.value() == 0

# Main loop
while True:
    # Check encoder button press to toggle LED on/off
    if debounce(rot_push):  # If the button is pressed
        led_on = not led_on  # Toggle LED state
        if not led_on:
            led.duty_u16(0)  # Turn off LED immediately if toggled off
        time.sleep(0.2)  # Small delay for debouncing
    
    # Process all available FIFO events
    while not fifo.empty():
        turn = fifo.get()  # Get integer value from FIFO
        
        if led_on:  # Only process turns if LED is on
            if turn == 1:  # Right turn
                # Increase brightness
                brightness = min(65535, brightness + 1000)
            else:  # Left turn (turn == 0)
                # Decrease brightness
                brightness = max(0, brightness - 1000)
            # Apply brightness to the LED
            led.duty_u16(brightness)
    
    # Small delay to avoid rapid polling
    time.sleep(0.01)  # Reduced delay to process FIFO more frequently