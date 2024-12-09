from machine import Pin, ADC, PWM
from piotimer import Piotimer as Timer
from fifo import Fifo
import time
import array  # Import the array module
from modules.kubios_mqtt import KubiosMQTT
from modules.display_manager import DisplayManager
from modules.hrv_analyzer import HRVAnalyzer

# Initialize hardware
adc = ADC(26)
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

# Initialize rotary encoder
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)

# Initialize other components
samplerate = 250
samples = Fifo(50)
current_selection = 0
menu_items = ["MEASURE HR", "HRV ANALYSIS", "KUBIOS", "HISTORY"]
history = []
max_history = 250
last_button_press = 0  # debouncing

# Initialize managers
display = DisplayManager()
hrv_analyzer = HRVAnalyzer()
kubios_mqtt = KubiosMQTT(
    "KME751_Group_4", 
    "takapenkinpojat",
    "192.168.4.57",
    "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a",
    "3pjgjdmamlj759te85icf0lucv",
    "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef",
    "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
)

def read_adc(tid):
    """
    Callback function to read ADC value and put it into the samples FIFO.
    Triggered by the timer at the specified sample rate.
    """
    samples.put(adc.read_u16())

tmr = Timer(freq=samplerate, callback=read_adc)

def encoder_turn_callback(pin):
    """
    Callback function for rotary encoder turn events.
    Puts a value into the samples FIFO based on the direction of the turn.
    """
    try:
        val = 0 if rota.value() == rotb.value() else 1
        samples.put(val)
    except:
        pass

def button_callback(pin):
    """
    Callback function for button press events.
    Implements debouncing and puts a value into the samples FIFO when the button is pressed.
    """
    global last_button_press
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_button_press) > 200:  # 200 ms debounce
        last_button_press = current_time
        try:
            samples.put(2)
        except:
            pass

rota.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_callback)
rot_push.irq(trigger=Pin.IRQ_FALLING, handler=button_callback)

# Initial menu display
display.display_menu(menu_items, current_selection)

def collect_ppi_data(duration=10):
    """
    Collects PPI (Pulse-to-Pulse Interval) data for a specified duration.
    Returns a list of ADC readings taken at 0.1-second intervals.
    """
    ppi_data = []
    start_time = time.ticks_ms()
    while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:
        ppi_data.append(adc.read_u16())
        time.sleep(0.1)
    return ppi_data

def measure_hr():
    def PPI_calc(data):
        sumPPI = sum(data)
        rounded_PPI = round(sumPPI / len(data), 0)
        return int(rounded_PPI)

    def HR(PPI):
        rounded_HR = round(60 * 1000 / PPI, 0)
        return int(rounded_HR)

    x1 = -1
    y1 = 32
    m0 = 65535 / 2
    a = 1 / 10

    disp_div = samplerate / 25
    disp_count = 0

    index = 0
    capture_count = 0
    subtract_old_sample = 0
    sample_sum = 0

    min_bpm = 30
    max_bpm = 200
    sample_peak = 0
    sample_index = 0
    previous_peak = 0
    previous_index = 0
    interval_ms = 0
    PPI_array = []
    
    brightness = 0

    avg_size = 128  # originally: int(samplerate * 0.5)
    buffer = array.array('H', [0] * avg_size)

    tmr = Timer(freq=samplerate, callback=read_adc)

    graph_points = []

    while True:
        if not samples.empty():
            x = samples.get()
            disp_count += 1

            if disp_count >= disp_div:
                disp_count = 0
                m0 = (1 - a) * m0 + a * x
                y2 = int(32 * (m0 - x) / 14000 + 35)
                y2 = max(10, min(53, y2))
                x2 = x1 + 1
                graph_points.append((x2, y2))

                display.oled.fill(0)
                display.oled.fill_rect(0, 0, 128, 9, 1)
                display.oled.fill_rect(0, 55, 128, 64, 1)
                if len(PPI_array) > 3:
                    actual_PPI = PPI_calc(PPI_array)
                    actual_HR = HR(actual_PPI)
                    display.oled.text(f'BPM: {actual_HR}', 2, 1, 0)
                display.oled.text(f'Timer: {int(capture_count / samplerate)}s', 18, 56, 0)
                
                # Draw the entire graph
                for i in range(1, len(graph_points)):
                    display.oled.line(graph_points[i-1][0], graph_points[i-1][1], graph_points[i][0], graph_points[i][1], 1)
                
                display.oled.show()

                x1 = x2 if x2 <= 127 else -1
                if x1 == -1:
                    graph_points = []
                y1 = y2

            old_sample = buffer[index] if subtract_old_sample else 0
            sample_sum = sample_sum + x - old_sample

            if subtract_old_sample:
                sample_avg = sample_sum / avg_size
                if x > (sample_avg * 1.05):
                    if x > sample_peak:
                        sample_peak = x
                        sample_index = capture_count
                else:
                    if sample_peak > 0:
                        if (sample_index - previous_index) > (60 * samplerate / min_bpm):
                            previous_peak = 0
                            previous_index = sample_index
                        elif sample_peak >= (previous_peak * 0.8):
                            if (sample_index - previous_index) > (60 * samplerate / max_bpm):
                                if previous_peak > 0:
                                    interval = sample_index - previous_index
                                    interval_ms = int(interval * 1000 / samplerate)
                                    PPI_array.append(interval_ms)
                                    brightness = 5
                                    led21.duty_u16(4000)
                                previous_peak = sample_peak
                                previous_index = sample_index
                    sample_peak = 0

                if brightness > 0:
                    brightness -= 1
                    if brightness == 0:
                        led21.duty_u16(0)

            buffer[index] = x
            capture_count += 1
            index = 0 if index >= avg_size - 1 else index + 1
            if index == 0:
                subtract_old_sample = 1

            # Check for button press to exit
            if rot_push.value() == 0:
                break

    tmr.deinit()

    while not samples.empty():
        samples.get()

    if len(PPI_array) >= 3:
        try:
            actual_PPI = PPI_calc(PPI_array)
            actual_HR = HR(actual_PPI)
            display.show_message([f'HR: {actual_HR} bpm'])
        except KeyboardInterrupt:
            machine.reset()

# Main loop
while True:
    if not samples.empty():
        event = samples.get()
    
        if event == 0:
            current_selection = (current_selection + 1) % len(menu_items)
            display.display_menu(menu_items, current_selection)
            
        elif event == 1:
            current_selection = (current_selection - 1) % len(menu_items)
            display.display_menu(menu_items, current_selection)
        
        elif event == 2:
            led_onboard.value(1)
            time.sleep(0.15)
            led_onboard.value(0)
            
            if current_selection == 0:  # "MEASURE HR"
                display.show_message(["Real-time HR", "Press to stop"])
                measure_hr()
                display.display_menu(menu_items, current_selection)
            
            elif current_selection == 1:  # "HRV ANALYSIS"
                display.show_message(["Collecting data..."])
                ppi_data = collect_ppi_data()
                
                mean_ppi = hrv_analyzer.meanPPI_calculator(ppi_data)
                sdnn = hrv_analyzer.SDNN_calculator(ppi_data, mean_ppi)
                rmssd = hrv_analyzer.RMSSD_calculator(ppi_data)
                mean_hr = hrv_analyzer.meanHR_calculator(mean_ppi)
                
                history.append(f"Mean PPI: {mean_ppi} ms")
                history.append(f"Mean HR: {mean_hr} bpm")
                history.append(f"SDNN: {sdnn} ms")
                history.append(f"RMSSD: {rmssd} ms")
                if len(history) > max_history:
                    history.pop(0)
                
                display.show_message([
                    "HRV ANALYSIS:",
                    f"Mean PPI: {mean_ppi} ms",
                    f"Mean HR: {mean_hr} bpm",
                    f"SDNN: {sdnn} ms",
                    f"RMSSD: {rmssd} ms"
                ])
                
                # Wait for button press to continue
                while True:
                    if not samples.empty() and samples.get() == 2:
                        break
                
            elif current_selection == 2:  # "KUBIOS"
                display.show_message(["KUBIOS CLOUD", "Measuring..."])
                ppi_data = collect_ppi_data()
                
                sns, pns = kubios_mqtt.analyze_data(ppi_data)
                if sns is not None and pns is not None:
                    display.show_message(["Results:", f"SNS: {sns}", f"PNS: {pns}"])
                else:
                    display.show_message(["Request failed"])
                
                # Wait for button press to continue
                while True:
                    if not samples.empty() and samples.get() == 2:
                        break
                
            elif current_selection == 3:  # "HISTORY"
                display.display_history(history)
                while True:
                    if not samples.empty() and samples.get() == 2:
                        break
            
            display.display_menu(menu_items, current_selection)
    
    time.sleep(0.01)


