from machine import I2C, Pin
from ssd1306 import SSD1306_I2C

class DisplayManager:
    def __init__(self):
        """
        Initializes the DisplayManager class with I2C and OLED settings.
        """
        self.OLED_WIDTH = 128
        self.OLED_HEIGHT = 64
        self.GRAPH_TOP = 16
        self.GRAPH_BUFFER_SIZE = 128
        
        # Initialize I2C and OLED
        i2c = I2C(1, sda=Pin(14), scl=Pin(15))
        self.oled = SSD1306_I2C(self.OLED_WIDTH, self.OLED_HEIGHT, i2c)
        self.graph_buffer = [0] * self.GRAPH_BUFFER_SIZE

    def display_menu(self, menu_items, current_selection):
        """
        Displays the menu items on the OLED screen, highlighting the current selection.
        """
        self.oled.fill(0)
        for i, item in enumerate(menu_items):
            y_pos = (i + 1) * 12
            if i == current_selection:
                self.oled.fill_rect(0, y_pos, 128, 12, 1)
                self.oled.text(item, 10, y_pos + 2, 0)
            else:
                self.oled.text(item, 10, y_pos + 2)
        self.oled.show()

    def update_graph(self, adc_value):
        """
        Updates the graph on the OLED screen with the latest ADC value.
        """
        scaled_value = int((adc_value / 65535) * self.OLED_HEIGHT)
        self.graph_buffer.pop(0)
        self.graph_buffer.append(scaled_value)
        
        self.oled.fill_rect(0, self.GRAPH_TOP, self.OLED_WIDTH, self.OLED_HEIGHT, 0)
        for x in range(1, len(self.graph_buffer)):
            self.oled.line(
                x - 1, self.GRAPH_TOP + self.OLED_HEIGHT - self.graph_buffer[x - 1],
                x, self.GRAPH_TOP + self.OLED_HEIGHT - self.graph_buffer[x],
                1
            )
        self.oled.show()

    def display_history(self, history):
        """
        Displays the history of HRV analysis results on the OLED screen.
        """
        self.oled.fill(0)
        self.oled.text("HISTORY", 0, 0, 1)
        for i, item in enumerate(history[-4:]):
            y_pos = (i + 1) * 8
            self.oled.text(f"{i + 1}: {item}", 0, y_pos, 1)
        self.oled.show()

    def show_message(self, messages, positions=None):
        """
        Displays a list of messages on the OLED screen at specified positions.
        """
        self.oled.fill(0)
        if positions is None:
            positions = [i * 16 for i in range(len(messages))]
        for message, pos in zip(messages, positions):
            self.oled.text(message, 0, pos)
        self.oled.show()