'''
Implement a program that plots the signal from the file on the OLED screen. The program must scale the
values automatically so that minimum and maximum values of the previous 250 samples will be the
minimum and maximum values used for scaling the next 250 samples to be plotted. Plotting is to scaled
so that minimum value plots a pixel at the bottom of the screen and maximum value at the top of the
screen. If scaled value would be outside the screen the value is capped to the limits.
• Less than 0 à 0
• Greater than 63 à 63
There are 250 data points per second and if you consider a typical heart rate in the range of 60-80 BPM
there will be 185 – 250 samples between peaks. This means that if you plot all samples, you will not be
able to see two beats on the screen because the screen is 128 pixels wide. To implement horizontal
scaling plot an average of five successive samples per pixel. That way the display will show 128 x 5 x 4ms
= 2560 ms of samples which is enough to display at least two peaks even at very low heart rates.
'''
from machine import Pin, I2C
import time
from filefifo import Filefifo
from ssd1306 import SSD1306_I2C

# Initialize I2C and OLED
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(128, 64, i2c)

# File and data settings
filename = "capture_250Hz_02.txt"
fifo = Filefifo(250, name=filename, repeat=True)
SAMPLE_RATE = 250  # samples per second
WINDOW_SIZE = 250  # sliding window for scaling
DISPLAY_WIDTH = 128  # OLED width in pixels
DISPLAY_HEIGHT = 64  # OLED height in pixels
SAMPLES_PER_PIXEL = 5  # average 5 samples per pixel on x-axis
PIXEL_HEIGHT_MAX = DISPLAY_HEIGHT - 1  # max y-pixel

# Initialize buffers
data_buffer = []
min_val = float('inf')
max_val = float('-inf')

def scale_value(value, min_val, max_val):
    """Scale value to OLED height, capped between 0 and DISPLAY_HEIGHT - 1."""
    if max_val > min_val:
        scaled = int((value - min_val) * PIXEL_HEIGHT_MAX / (max_val - min_val))
    else:
        scaled = PIXEL_HEIGHT_MAX // 2  # fallback if min equals max
    return min(max(scaled, 0), PIXEL_HEIGHT_MAX)  # Cap between 0 and max display height

def get_scaled_data_points(data, window_size, samples_per_pixel):
    """Return scaled y-values for OLED plotting, averaged by samples_per_pixel."""
    scaled_points = []
    for i in range(0, len(data), samples_per_pixel):
        avg_value = sum(data[i:i + samples_per_pixel]) / samples_per_pixel
        scaled_y = scale_value(avg_value, min_val, max_val)
        scaled_points.append(scaled_y)
    return scaled_points

def update_min_max():
    """Update global min and max values from the latest 250 samples."""
    global min_val, max_val
    min_val = min(data_buffer)
    max_val = max(data_buffer)

def display_data():
    """Clear and plot data on OLED."""
    oled.fill(0)
    scaled_points = get_scaled_data_points(data_buffer, WINDOW_SIZE, SAMPLES_PER_PIXEL)
    for x, y in enumerate(scaled_points):
        oled.pixel(x, DISPLAY_HEIGHT - 1 - y, 1)  # Plot from bottom up
    oled.show()

def main():
    print("Starting to display data...")
    while True:
        # Fill data buffer with 250 new samples
        data_buffer.clear()
        for _ in range(WINDOW_SIZE):
            data_point = float(fifo.get())
            data_buffer.append(data_point)
        
        # Update scaling range with new data
        update_min_max()
        
        # Display data on the OLED
        display_data()
        
        time.sleep(0.01)  # slight delay for visibility

if __name__ == "__main__":
    main()
