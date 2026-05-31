import network
import time
import dht
from umqtt.simple import MQTTClient
from machine import Pin
import random  # <-- função de randomização da temperatura para testes

# --- Configuração dos LEDs ---
led_green = Pin(2, Pin.OUT)
led_red   = Pin(4, Pin.OUT)

led_red.value(1)

def set_led(accepted: bool):


    if accepted:
        led_green.value(1)
        led_red.value(0)
        print("[LED] GREEN - Accepted")
    else:
        led_green.value(0)
        led_red.value(1)
        print("[LED] RED - Rejected")


def on_message(topic, msg):
    print("Response received on [{}]: {}".format(topic.decode(), msg.decode()))
    
    if msg == b"ON":
        set_led(accepted=True)
    elif msg == b"OFF":
        set_led(accepted=False)
    else:
        print("[LED] Unknown response — blinking both LEDs")
        for _ in range(3):
            led_green.value(1)
            led_red.value(1)
            time.sleep(0.3)
            led_green.value(0)
            led_red.value(0)
            time.sleep(0.3)


def connect_wifi():
    print("Connecting Wi-Fi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Wokwi-GUEST', '')
      
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.1)
      
    print(" Successful connection!")


def connect_mqtt_server():
    print("\nConnecting to MQTT server", end="")
    client = MQTTClient(
        client_id=b"100",
        server=b"420fea555ede4bd4a100b1da5ef2a840.s1.eu.hivemq.cloud",
        port=8883,
        user=b"fieldhub",
        password=b"Fieldhub@2025",
        ssl=True,
        ssl_params={"server_hostname": "420fea555ede4bd4a100b1da5ef2a840.s1.eu.hivemq.cloud"}
    )

    client.set_callback(on_message)
    client.connect()
    client.subscribe(b"irrigacao/comando")
    print(". . .Successful connection!")
    print("Subscribed to [irrigacao/comando]")

    return client


def read_sensor(dht22, last_temp, last_hum):
    """
    Tenta ler o sensor DHT22. Se falhar, aplica uma variação
    aleatória pequena sobre a última leitura válida.
    Sempre adiciona um ruído suave para simular variações reais.
    
    Faixas realistas para lavoura:
      - Temperatura: 18°C a 38°C
      - Umidade:     30% a 95%
    """
    try:
        dht22.measure()
        temp = dht22.temperature()
        hum  = dht22.humidity()
    except Exception:
        temp = last_temp
        hum  = last_hum

    # Variação aleatória suave a cada leitura (±0.5°C e ±1.5%)
    temp += random.uniform(-0.5, 0.5)
    hum  += random.uniform(-1.5, 1.5)

    # Mantém dentro de faixas realistas
    temp = max(18.0, min(38.0, temp))
    hum  = max(30.0, min(95.0, hum))

    # Arredonda para 1 casa decimal
    return round(temp, 1), round(hum, 1)


def main():
    connect_wifi()
    mqtt_client = connect_mqtt_server()

    dht22 = dht.DHT22(Pin(5))

    # Valores iniciais realistas como ponto de partida
    last_temp = round(random.uniform(22.0, 30.0), 1)
    last_hum  = round(random.uniform(50.0, 80.0), 1)

    while True:
        temp, hum = read_sensor(dht22, last_temp, last_hum)

        message = "DHT22,id=100 temperature={},humidity={}".format(temp, hum)
        print("Envio de dados para Requisição: " + message)

        try:
            mqtt_client.publish(b"irrigacao/sensores", message)
        except Exception as e:
            print("Erro no envio MQTT:", e)

        last_temp = temp
        last_hum  = hum

        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                mqtt_client.check_msg()
            except Exception as e:
                print("Error checking MQTT messages:", e)
            time.sleep(0.2)


if __name__ == "__main__":
    main()
