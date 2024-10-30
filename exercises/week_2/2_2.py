from filefifo import Filefifo

# Constants
SAMPLE_RATE = 250  # Hz
TWO_SECONDS = SAMPLE_RATE * 2  # First two seconds for min-max calculation
TEN_SECONDS = SAMPLE_RATE * 10  # Total time to plot (10 seconds)

# Initialize Filefifo instance
data = Filefifo(10, name='capture_250Hz_01.txt')

# Step 1: Read two seconds of data to find min and max
first_two_seconds = [data.get() for _ in range(TWO_SECONDS)]
min_value = min(first_two_seconds)
max_value = max(first_two_seconds)

# Check for valid range to avoid division by zero
if max_value == min_value:
    print("Data has no variation; all values are the same.")
else:
    # Step 2: Scale the next 10 seconds of data to 0–100
    print("Scaled Data (0 to 100):")
    for _ in range(TEN_SECONDS):
        original_value = data.get()
        # Scale the value
        scaled_value = (original_value - min_value) / (max_value - min_value) * 100
        print(scaled_value)