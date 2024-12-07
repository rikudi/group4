from machine import Pin, ADC, PWM
from piotimer import Piotimer as Timer
from fifo import Fifo
import time
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
    "192.168.4.253",
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
                while True:
                    display.update_graph(adc.read_u16())
                    if not samples.empty() and samples.get() == 2:
                        break
                    time.sleep(0.01)
                    
            elif current_selection == 1:  # "HRV ANALYSIS"
                display.show_message(["Collecting data..."])
                ppi_data = collect_ppi_data()
                
                mean_ppi = hrv_analyzer.meanPPI_calculator(ppi_data)
                sdnn = hrv_analyzer.SDNN_calculator(ppi_data, mean_ppi)
                rmssd = hrv_analyzer.RMSSD_calculator(ppi_data)
                
                history.append(f"SDNN: {sdnn} ms")
                history.append(f"RMSSD: {rmssd} ms")
                if len(history) > max_history:
                    history.pop(0)
                
                display.show_message(["HRV ANALYSIS:", f"SDNN: {sdnn} ms", f"RMSSD: {rmssd} ms"])
                time.sleep(2)
                
            elif current_selection == 2:  # "KUBIOS"
                display.show_message(["KUBIOS TEST", "Sending..."])
                ppi_data = collect_ppi_data()
                
                sns, pns = kubios_mqtt.analyze_data(ppi_data)
                
                if sns is not None and pns is not None:
                    display.show_message(["Results:", f"SNS: {sns}", f"PNS: {pns}"])
                else:
                    display.show_message(["Request failed"])
                time.sleep(2)
                
            elif current_selection == 3:  # "HISTORY"
                display.display_history(history)
                while True:
                    if not samples.empty() and samples.get() == 2:
                        break
            
            display.display_menu(menu_items, current_selection)
    
    time.sleep(0.01)


