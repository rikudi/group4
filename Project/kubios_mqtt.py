import urequests as requests
import ujson
import network
import time
from umqtt.simple import MQTTClient

class KubiosMQTT:
    def __init__(self, ssid, password, mqtt_server, api_key, client_id, client_secret, token_url):
        """
        Initializes the KubiosMQTT class with WiFi, MQTT, and API credentials.
        """
        self.ssid = ssid
        self.password = password
        self.mqtt_server = mqtt_server
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.wlan = None
        self.mqtt = None

    def connect_wifi(self):
        """
        Connects to the WiFi network using the provided SSID and password.
        """
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if not self.wlan.isconnected():
            print("Connecting to WiFi...")
            self.wlan.connect(self.ssid, self.password)
            while not self.wlan.isconnected():
                time.sleep(0.1)
        print("Network connected")

    def disconnect_wifi(self):
        """
        Disconnects from the WiFi network.
        """
        if self.wlan:
            try:
                self.wlan.disconnect()
                self.wlan.active(False)
            except:
                pass

    def connect_mqtt(self):
        """
        Connects to the MQTT server.
        """
        self.mqtt = MQTTClient("pico", self.mqtt_server)
        self.mqtt.connect()

    def disconnect_mqtt(self):
        """
        Disconnects from the MQTT server.
        """
        if self.mqtt:
            try:
                self.mqtt.disconnect()
            except:
                pass

    def get_auth_token(self):
        """
        Requests an authentication token from the Kubios API.
        """
        print("\nRequesting auth token...")
        auth_response = requests.post(
            self.token_url,
            data='grant_type=client_credentials&client_id={}'.format(self.client_id),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            auth=(self.client_id, self.client_secret)
        )
        print("Auth response:", auth_response.text)
        access_token = auth_response.json()["access_token"]
        print("Access token received")
        return access_token

    def analyze_data(self, ppi_data):
        """
        Analyzes PPI data using the Kubios API and publishes the results to the MQTT server.
        """
        try:
            self.connect_wifi()
            self.connect_mqtt()

            access_token = self.get_auth_token()

            dataset = {
                "id": 123,
                "type": "RRI",
                "data": ppi_data,
                "analysis": {
                    "type": "readiness"
                }
            }

            print("Dataset:", dataset)
            response = requests.post(
                "https://analysis.kubioscloud.com/v2/analytics/analyze",
                headers={
                    "Authorization": "Bearer {}".format(access_token),
                    "X-Api-Key": self.api_key
                },
                json=dataset
            )

            result = response.json()
            print("\nAnalysis Results:")
            print("-----------------")
            print("Response status:", response.status_code)
            print("Full response:", result)
            print("\nExtracted values:")
            sns = result['analysis'].get('sns_index', 'N/A')
            pns = result['analysis'].get('pns_index', 'N/A')
            print("SNS:", sns)
            print("PNS:", pns)
            print("=== Analysis Complete ===\n")

            mqtt_message = ujson.dumps({
                'sns': sns,
                'pns': pns,
                'timestamp': time.time()
            })
            self.mqtt.publish('test', mqtt_message)
            print("Published to MQTT:", mqtt_message)

            return sns, pns

        except Exception as e:
            print("\nKubios analysis error:", str(e))
            print("=== Analysis Failed ===\n")
            return None, None

        finally:
            self.disconnect_mqtt()
            self.disconnect_wifi()