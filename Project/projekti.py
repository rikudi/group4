from machine import Pin, I2C, ADC, PWM
from piotimer import Piotimer as Timer
from ssd1306 import SSD1306_I2C 
from fifo import Fifo
import urequests as requests
import ujson
import network
import utime
import array
import time
import socket


#ADC-converter
adc = ADC(26)

OLED_WIDTH = 128
OLED_HEIGHT = 64

#Initialize I2C and OLED
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# Constants for the OLED graph
GRAPH_WIDTH = OLED_WIDTH
GRAPH_HEIGHT = OLED_HEIGHT  # Height of the graph area
GRAPH_TOP = 16  # Vertical offset for the graph
GRAPH_BUFFER_SIZE = GRAPH_WIDTH  # Buffer size matches the width of the display

# Buffer to store ADC values for the graph
graph_buffer = [0] * GRAPH_BUFFER_SIZE  # Pre-fill with zeros

#LEDs
led_onboard = Pin("LED", Pin.OUT)
led21 = PWM(Pin(21))
led21.freq(1000)

#Initialize rotary encoder pins
rota = Pin(10, Pin.IN, Pin.PULL_UP)
rotb = Pin(11, Pin.IN, Pin.PULL_UP)
rot_push = Pin(12, Pin.IN, Pin.PULL_UP)

# Sample rate and buffer
samplerate = 250
samples = Fifo(50)

# Menu selection variables
current_selection = 0

last_button_time = 0
DEBOUNCE_MS = 500

menu_items = ["MEASURE HR", "HRV ANALYSIS", "KUBIOS", "HISTORY"]

max_history = 250
history = []

# ei käytössä
PPI_array = []

APIKEY = "pbZRUi49X48I56oL1Lq8y8NDjq6rPfzX3AQeNo3a"
CLIENT_ID = "3pjgjdmamlj759te85icf0lucv"
CLIENT_SECRET = "111fqsli1eo7mejcrlffbklvftcnfl4keoadrdv1o45vt9pndlef" 

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"

ssid = "KME751_Group_4"
password = "takapenkinpojat"

ppi_data = []  # Initialize PPI data buffer

# Function to collect PPI data dynamically
def collect_ppi_data(duration=10):
    global ppi_data
    start_time = time.ticks_ms()
    ppi_data = []  # Clear existing data
    while time.ticks_diff(time.ticks_ms(), start_time) < duration * 1000:  # Collect data for `duration` seconds
        ppi_data.append(adc.read_u16())
        time.sleep(0.1)
        
def create_kubios_dataset(ppi_data):
    return {
        "type": "RR",
        "data": ppi_data,
        "analysis_type": "readiness"  # Adjust this to your desired analysis type
    }

#Ei käytössä vielä missään
def send_kubios_request(dataset, access_token):
    response = requests.post(
        url="https://analysis.kubioscloud.com/v1/analysis/readiness",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Api-Key": APIKEY
        },
        json=dataset
    )
    return response.json()

#Ei käytössä vielä missään
# Signal reading function
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)

tmr = Timer(freq = samplerate, callback = read_adc)

def encoder_turn_callback(pin):
    try:
        if rota.value() == rotb.value():
            samples.put(1)
        else:
            samples.put(0)
    except RuntimeError:
        pass
    
#Ei käytössä vielä
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    ip = wlan.ifconfig()[0]
    return ip

def button_callback(pin):
    global last_button_time
    current_time = time.ticks_ms()
    
    #Check if enough time has passed since last press
    if time.ticks_diff(current_time, last_button_time) > DEBOUNCE_MS:
        try:
            samples.put(2) # Button press event
            last_button_time = current_time
        except RuntimeError:
            pass

rota.irq(trigger=Pin.IRQ_RISING, handler=encoder_turn_callback)
rot_push.irq(trigger=Pin.IRQ_FALLING, handler=button_callback)

# PPI Calculator
def meanPPI_calculator(data):
    sumPPI = 0
    for i in data:
        sumPPI += 1
    rounded_PPI = round(sumPPI/len(data), 0)
    return int(rounded_PPI)

# HR Calculator
def meanHR_calculator(meanPPI):
    rounded_HR = round(60*1000/meanPPI, 0)
    return int(rounded_HR)

# SDNN Calculator
def SDNN_calculator(data, PPI):
    summary = 0
    for i in data:
        summary += (i-PPI)**2
    SDNN = (summary/(len(data)-1))**(1/2)
    rounded_SDNN = round(SDNN, 0)
    return int(rounded_SDNN)

# RMSSD Calculator
def RMSSD_calculator(data):
    i = 0
    summary = 0
    while i < len(data)-1:
        summary += (data[i+1]-data[i])**2
        i +=1
    rounded_RMSSD = round((summary/(len(data)-1))**(1/2), 0)
    return int(rounded_RMSSD)

# Ei käytössä vielä
# SDSD Calculator
def SDSD_calculator(data):
    PP_array = array.array('l')
    i = 0
    first_value = 0
    second_value = 0
    while i < len(data)-1:
        PP_array.append(int(data[i+1])-int(data[i]))
        i += 1
    i = 0
    while i < len(PP_array)-1:
        first_value += float(PP_array[i]**2)
        second_value += float(PP_array[i])
        i += 1
    first = first_value/(len(PP_array)-1)
    second = (second_value/(len(PP_array)))**2
    rounded_SDSD = round((first - second)**(1/2), 0)
    return int(rounded_SDSD)

# Ei käytössä vielä
# SD1 Calculator
def SD1_calculator(SDSD):
    rounded_SD1 = round(((SDSD**2)/2)**(1/2), 0)
    return int(rounded_SD1)

# Ei käytössä vielä
# SD2 Calculator
def SD2_calculator(SDNN, SDSD):
    rounded_SD2 = round(((2*(SDNN**2))-((SDSD**2)/2))**(1/2), 0)
    return int(rounded_SD2)

# History function
def display_history():
    oled.fill(0) # Clear display
    
    #Title
    oled.text("HISTORY", 0, 0, 1)
    
    # Display 5 items from history
    for i, item in enumerate(history[-4:]): # show last 4
        y_pos = (i + 1) * 8 # Adjust vertical spacing
        oled.text(f"{i + 1}: {item}", 0, y_pos, 1) # Display history item
        
    oled.show()
    
    #Tää paska ei toimi vissii
'''
def get_kubios_token():
    response = requests.post(
        url=TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response_data = response.json()
    return response_data["access_token"]
'''

# Function to update the graph
def update_graph(adc_value):
    global graph_buffer

    # Scale ADC value to fit graph height
    scaled_value = int((adc_value / 65535) * GRAPH_HEIGHT)

    # Update buffer (FIFO behavior)
    graph_buffer.pop(0)  # Remove oldest value
    graph_buffer.append(scaled_value)  # Add new value

    # Clear the graph area
    oled.fill_rect(0, GRAPH_TOP, GRAPH_WIDTH, GRAPH_HEIGHT, 0)

    # Draw the graph line
    for x in range(1, len(graph_buffer)):
        oled.line(
            x - 1, GRAPH_TOP + GRAPH_HEIGHT - graph_buffer[x - 1],  # Start point
            x, GRAPH_TOP + GRAPH_HEIGHT - graph_buffer[x],  # End point
            1  # Color (white)
        )
    oled.show()

def display_menu():
    oled.fill(0) # Clear display
    
    for i, item in enumerate(menu_items):
        y_pos = (i + 1) * 12 # Space items vertically
        # Show selection arrow
        if i == current_selection:
            oled.fill_rect(0, y_pos, 128, 12, 1) #Highlight selected row
            oled.text(item, 10, y_pos + 2, 0) # White text on black background
        else:
            oled.text(item, 10, y_pos +2) # Normal text
            
    oled.show() # Update display
    
# Initial menu display
display_menu()


'''
response = requests.post(
    url = TOKEN_URL,
    data = 'grant_type=client_credentials&client_id={}'.format(CLIENT_ID),
    headers = {'Content-Type':'application/x-www-form-urlencoded'},
    auth = (CLIENT_ID, CLIENT_SECRET))
response = response.json() #Parse JSON response into a python dictionary 
access_token = response["access_token"] #Parse access token

#Interval data to be sent to Kubios Cloud. Replace with your own data:
intervals = [828, 836, 852, 760, 800, 796, 856, 824, 808, 776, 724, 816, 800, 812, 812, 812,
756, 820, 812, 800] 

#Create the dataset dictionary HERE

# Make the readiness analysis with the given data
response = requests.post(
    url = ""
    headers = { "authorization": "Bearer {}".format(access_token), #use access token to access your Kubios Cloud analysis session
               "X-Api-Key": APIKEY},
    json = dataset) #dataset will be automatically converted to JSON by the urequests library
response = response.json()

#Print out the SNS and PNS values on the OLED screen here
'''


while True:
    if not samples.empty():
        event = samples.get()
    
        if event == 0:
            current_selection = (current_selection +1) % len(menu_items)
            display_menu()
            
        elif event == 1:
            current_selection = (current_selection -1) % len(menu_items)
            display_menu()
        
        elif event == 2:
            led_onboard.value(1)
            time.sleep(0.15)
            led_onboard.value(0)
            
            if current_selection == 0:  # "MEASURE HR"
                oled.fill(0)
                oled.text("Real-time HR", 0, 0)
                oled.text("Press to stop", 0, 8)
                tmr.deinit()
                oled.show()

                start_time = time.ticks_ms()
                while True:
                    # Read ADC value
                    adc_value = adc.read_u16()

                    # Update the real-time graph
                    update_graph(adc_value)

                    # Exit on button press
                    if not samples.empty():
                        event = samples.get()
                        if event == 2:  # Button pressed
                            break

                    # Limit the sampling rate (optional, adjust as needed)
                    time.sleep(0.01)

                display_menu()

            if current_selection == 1:  # "HRV ANALYSIS"
                oled.fill(0)
                oled.text("Collecting data...", 0, 0)
                oled.show()
                collect_ppi_data()  # Collect dynamic PPI data

                mean_ppi = meanPPI_calculator(ppi_data)
                sdnn = SDNN_calculator(ppi_data, mean_ppi)
                rmssd = RMSSD_calculator(ppi_data)

                history.append(f"SDNN: {sdnn} ms")
                history.append(f"RMSSD: {rmssd} ms")
                if len(history) > max_history:
                    history.pop(0)

                oled.fill(0)
                oled.text("HRV ANALYSIS:", 0, 0)
                oled.text(f"SDNN: {sdnn} ms", 0, 16)
                oled.text(f"RMSSD: {rmssd} ms", 0, 32)
                oled.show()
                time.sleep(2)
                display_menu()

                
            if current_selection == 2:  # "KUBIOS"
                oled.fill(0)
                oled.text("Collecting data...", 0, 0)
                oled.show()
                collect_ppi_data()  # Collect dynamic PPI data

                dataset = create_kubios_dataset(ppi_data)
                
                # Pitää selvittää miks tää antaa errorin
                try:
                    response = requests.post(
                        url="https://analysis.kubioscloud.com/v1/analysis/readiness",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "X-Api-Key": APIKEY
                        },
                        json=dataset
                    )
                    analysis_result = response.json()

                    # Extract results (example)
                    sns = analysis_result.get("sns", "N/A")
                    pns = analysis_result.get("pns", "N/A")

                    # Add results to history
                    history.append(f"SNS: {sns}")
                    history.append(f"PNS: {pns}")
                    if len(history) > max_history:
                        history.pop(0)

                    # Display results
                    oled.fill(0)
                    oled.text("KUBIOS RESULTS:", 0, 0)
                    oled.text(f"SNS: {sns}", 0, 16)
                    oled.text(f"PNS: {pns}", 0, 32)
                    oled.show()
                    time.sleep(2)

                except Exception as e:
                    oled.fill(0)
                    oled.text("API ERROR", 0, 0)
                    oled.text(str(e), 0, 16)
                    oled.show()
                    time.sleep(2)

                display_menu()

            
            if current_selection == len(menu_items) - 1: # if history is selected
                display_history()
                
                # Return menu
                while True:
                    if not samples.empty():
                        event = samples.get()
                        if event == 2:
                            display_menu()
                            break
            else:
                display_menu()
            
            display_menu()
    
    time.sleep(0.01)


