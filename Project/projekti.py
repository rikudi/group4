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

#Initialize I2C and OLED
i2c = I2C(1, sda=Pin(14), scl=Pin(15))
oled = SSD1306_I2C(128, 64, i2c)

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

# Menu selevtion variables and switch filtering
current_selection = 0

last_button_time = 0
DEBOUNCE_MS = 500

menu_items = ["MEASURE HR", "HRV ANALYSIS", "KUBIOS", "HISTORY"]

max_history = 250
history = []

'''
#SSID credentials
ssid = ""
password = "Takapenkinpojat1234"
'''

# Kuios credentials
APIKEY = ""
CLIENT_ID =""
CLIENT_SECRET = ""

LOGIN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/login"
TOKEN_URL = "https://kubioscloud.auth.eu-west-1.amazoncognito.com/oauth2/token"
REDIRECT_URI = "https://analysis.kubioscloud.com/v1/portal/login"


# Signal reading function
def read_adc(tid):
    x = adc.read_u16()
    samples.put(x)


def encoder_turn_callback(pin):
    try:
        if rota.value() == rotb.value():
            samples.put(1)
        else:
            samples.put(0)
    except RuntimeError:
        pass
    
def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
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

# SD1 Calculator
def SD1_calculator(SDSD):
    rounded_SD1 = round(((SDSD**2)/2)**(1/2), 0)
    return int(rounded_SD1)

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
    for i, item in enumerate(history[-5:]): # show last 5
        y_pos = (i + 1) * 12 # Adjust vertical spacing
        oled.text(f"{i + 1}: {item}", 0, y_pos, 1) # Display history item
        
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
                ppi_data = [828, 836, 852, 760, 800]  # Replace with real PPI data
                mean_ppi = meanPPI_calculator(ppi_data)
                hr = meanHR_calculator(mean_ppi)  # Calculate HR
                history.append(f"HR: {hr} BPM")  # Add result to history
                
                # Limit the history size
                if len(history) > max_history:
                    history.pop(0)  # Remove the oldest entry

                # Display the result on OLED (example display)
                oled.fill(0)
                oled.text("MEASURED HR:", 0, 0)
                oled.text(f"{hr} BPM", 0, 16)
                oled.show()
                time.sleep(2)
                display_menu()  # Return to menu
                
            if current_selection == 1:  # "HRV ANALYSIS"
                ppi_data = [828, 836, 852, 760, 800]  # Replace with real PPI data
                mean_ppi = meanPPI_calculator(ppi_data)
                sdnn = SDNN_calculator(ppi_data, mean_ppi)
                rmssd = RMSSD_calculator(ppi_data)

                # Add results to history
                history.append(f"SDNN: {sdnn} ms")
                history.append(f"RMSSD: {rmssd} ms")

                # Limit the history size
                while len(history) > max_history:
                    history.pop(0)

                # Display results on OLED (example display)
                oled.fill(0)
                oled.text("HRV ANALYSIS:", 0, 0)
                oled.text(f"SDNN: {sdnn} ms", 0, 16)
                oled.text(f"RMSSD: {rmssd} ms", 0, 32)
                oled.show()
                time.sleep(2)
                display_menu()  # Return to menu
                
            if current_selection == 2:  # "KUBIOS" 
                intervals = [828, 836, 852, 760, 800]  # Replace with real interval data

                # Example of response parsing (mock API result)
                sns = 0.65  # Replace with actual API response value
                pns = 0.35  # Replace with actual API response value
                
                # Add results to history
                history.append(f"SNS: {sns}")
                history.append(f"PNS: {pns}")
                
                # Limit history size
                while len(history) > max_history:
                    history.pop(0)

                # Display results on OLED
                oled.fill(0)
                oled.text("KUBIOS RESULTS:", 0, 0)
                oled.text(f"SNS: {sns}", 0, 16)
                oled.text(f"PNS: {pns}", 0, 32)
                oled.show()
                time.sleep(2)
                display_menu()  # Return to menu
            
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
