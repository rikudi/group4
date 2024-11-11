from filefifo import Filefifo

def calculate_moving_average(data, window_size):
    """Calculate a simple moving average."""
    avg_values = []
    half_window = window_size // 2
    
    for i in range(len(data)):
        # Define window boundaries
        start = max(0, i - half_window)
        end = min(len(data), i + half_window)
        
        # Calculate average and append to result list
        window_avg = sum(data[start:end]) / (end - start)
        avg_values.append(window_avg)
    
    return avg_values

def detect_peaks(data, threshold_factor=0.6):
    """Detect peaks by comparing each point to a threshold based on moving average."""
    moving_avg = calculate_moving_average(data, 25)  # 25 samples (~100ms at 250Hz)
    peaks = []
    
    for i in range(1, len(data) - 1):
        threshold = moving_avg[i] * threshold_factor
        # Check if current point is a peak and exceeds the threshold
        if data[i] > data[i - 1] and data[i] > data[i + 1] and data[i] > threshold:
            peaks.append(i)
    
    return peaks

def calculate_heart_rate(peaks, sampling_rate=250):
    """Calculate heart rate from time intervals between detected peaks."""
    if len(peaks) < 2:
        return None
    
    # Calculate average interval between peaks (in seconds)
    intervals = [peaks[i] - peaks[i - 1] for i in range(1, len(peaks))]
    avg_interval_sec = sum(intervals) / len(intervals) / sampling_rate
    
    # Calculate heart rate in BPM (beats per minute)
    return round(60 / avg_interval_sec)

def main():
    # Initialize file and data variables
    filename = "capture_250Hz_02.txt"
    fifo = Filefifo(750, 'H', filename, repeat=True)  # 750 samples = 3 seconds at 250Hz
    heart_rates = []
    data_buffer = []
    
    print("Processing data and calculating heart rates...")
    
    # Loop to collect and process heart rates until 20 are detected
    while len(heart_rates) < 20:
        try:
            # Retrieve data from file and add to buffer
            data_buffer.append(fifo.get())
            
            # Process data buffer when it reaches desired length
            if len(data_buffer) >= 750:
                peaks = detect_peaks(data_buffer)
                hr = calculate_heart_rate(peaks)
                
                # Store and print valid heart rates
                if hr is not None and 40 <= hr <= 200:
                    heart_rates.append(hr)
                    print(f"Detected Heart Rate: {hr} BPM")
                
                # Keep half the buffer data to maintain continuity
                data_buffer = data_buffer[375:]
        
        except RuntimeError as e:
            if "Out of data" in str(e):
                break
            else:
                print(f"Runtime error: {e}")
                break
    
    # Print summary if heart rates were detected
    if heart_rates:
        print("\nSummary:")
        print(f"Average Heart Rate: {sum(heart_rates) / len(heart_rates):.1f} BPM")
        print(f"Min Heart Rate: {min(heart_rates)} BPM")
        print(f"Max Heart Rate: {max(heart_rates)} BPM")
    else:
        print("Could not detect enough valid heart rates from the data.")

if __name__ == "__main__":
    main()
