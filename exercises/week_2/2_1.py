from filefifo import Filefifo

SAMPLE_RATE = 250 # Hz
NUM_DATA_POINTS = 3000 # Number of data points to read from filefifo

# Initialize Filefifo instance
data = Filefifo(10, name = 'capture_250Hz_01.txt')
    
# Variables to track peaks
peaks = []
previous_value = data.get()
previous_slope_positive = None

for i in range(NUM_DATA_POINTS):
    current_value = data.get()
    
    # Calculate the slope
    slope = current_value - previous_value
        
    #Check for positive to negative slope change
    if previous_slope_positive and slope < 0:
        # Store the sample index of the peak
        peaks.append(i - 1)
    
    # Update variables for the next iteration
    previous_value = current_value
    previous_slope_positive = slope > 0
    
# Calculate intervals between peaks and convert to seconds
if len(peaks) < 2:
    print("Not enough peaks detected.")
else:
    print("Peak-to-Peak Intervals: ")
    for i in range(1, min(len(peaks), 4)):
        interval_samples = peaks[i] - peaks[i-1]
        interval_seconds = interval_samples / SAMPLE_RATE
        frequency = 1 / interval_seconds
        print(f"Interval {i}: {interval_samples} samples, {interval_seconds:.4f} seconds, Frequency: {frequency:.2f} Hz")