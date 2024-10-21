from machine import Pin, I2C
import ssd1306
import utime

# Määritellään näytön koko
OLED_WIDTH = 128
OLED_HEIGHT = 64

# Määritellään UFO:n koko ja alkuasento
UFO_WIDTH = 24
UFO_HEIGHT = 8
ufo_x = 0  # UFO:n alkupiste

# Määritellään nappien GPIO-pinnit (säädä oman kytkentäsi mukaisesti)
SW0 = Pin(9, Pin.IN, Pin.PULL_UP)  # SW0 on GPIO12
SW2 = Pin(7, Pin.IN, Pin.PULL_UP)  # SW2 on GPIO13

# I2C-määritykset OLED-näytölle (sama kuin aiemmin)
i2c = I2C(1, scl=Pin(15), sda=Pin(14), freq=400000)

# Luodaan OLED-näytön olio (ssd1306-kirjasto)
oled = ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# Funktio UFO:n piirtämiseksi
def draw_ufo(x):
    oled.fill(0)  # Tyhjennetään näyttö
    oled.text("<=>", x, OLED_HEIGHT - UFO_HEIGHT)  # Piirretään UFO alaosaan
    oled.show()

# Funktio päivittää UFO:n sijaintia
def update_ufo_position(move_right):
    global ufo_x
    if move_right and (ufo_x + UFO_WIDTH) < OLED_WIDTH:
        ufo_x += 8  # Liikutetaan oikealle 8 pikselin verran
    elif not move_right and ufo_x > 0:
        ufo_x -= 8  # Liikutetaan vasemmalle 8 pikselin verran
    draw_ufo(ufo_x)

# Alustetaan UFO aloituskohtaan
draw_ufo(ufo_x)

# Pääsilmukka
while True:
    if SW0.value() == 0:  # SW0 painettuna (liikuta oikealle)
        print("SW0 painettu, UFO liikkuu oikealle")
        update_ufo_position(True)
        
    if SW2.value() == 0:  # SW2 painettuna (liikuta vasemmalle)
        print("SW2 painettu, UFO liikkuu vasemmalle")
        update_ufo_position(False)
        
