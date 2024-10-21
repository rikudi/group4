from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Alustetaan I2C ja OLED-näyttö
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

buffer = []
max_lines = oled.height // 8  # Rivien määrä, OLED:n korkeuden perusteella

def update_display():
    oled.fill(0)
    for i, line in enumerate(buffer[-max_lines:]):  # Näytetään vain viimeiset max_lines
        oled.text(line, 0, i * 8)
    oled.show()

while True:
    user_input = input("Enter text: ")
    buffer.append(user_input)  # Lisää uusi rivi
    if len(buffer) > max_lines:
        buffer.pop(0)  # Poista vanhin rivi
    update_display()  # Päivitä näyttö
    time.sleep(0.1)