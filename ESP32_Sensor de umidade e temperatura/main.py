""" 
Importação da bibliotecas necessarias para a conexão:
    - Conectar a internet (network)
    - Obter data e hora (time)
    - Ler os dados do sensor DHT22 (dht) conectado em um pin especifico (Pin)
    - Usar o protocolo MQTT (umqtt)
"""
import network
import time
import dht
from umqtt.simple import MQTTClient
from machine import Pin


# --- Configuração dos LEDs ---
led_green = Pin(2, Pin.OUT)  # Aceito
led_red   = Pin(4, Pin.OUT)  # Rejeitado

def set_led(accepted: bool):
    """
    Acende o LED correspondente por 3 segundos e apaga ambos em seguida.
    - Verde (pino 2): requisição aceita
    - Vermelho (pino 4): requisição rejeitada
    """
    if accepted:
        led_green.value(1)
        led_red.value(0)
        print("[LED] GREEN - Accepted")
    else:
        led_green.value(0)
        led_red.value(1)
        print("[LED] RED - Rejected")
    
    time.sleep(3)
    led_green.value(0)
    led_red.value(0)


def on_message(topic, msg):
    """
    Callback chamado automaticamente quando o ESP32 recebe uma mensagem
    no tópico assinado (DHT22_response).
    
    Espera receber: b"On" ou b"Off"
    """
    print("Response received on [{}]: {}".format(topic.decode(), msg.decode()))
    
    if msg == b"ON":
        set_led(accepted=True)
    elif msg == b"OFF":
        set_led(accepted=False)
    else:
        # Resposta inesperada: pisca os dois LEDs como aviso
        print("[LED] Unknown response — blinking both LEDs")
        for _ in range(3):
            led_green.value(1)
            led_red.value(1)
            time.sleep(0.3)
            led_green.value(0)
            led_red.value(0)
            time.sleep(0.3)


def connect_wifi():
    """
    Esta função inclui tudo o que é necessário para conectar-se à rede Wi-Fi Wokwi.
    Imprime um ponto (.) até que a conexão seja estabelecida.
    """
    print("Connecting Wi-Fi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Wokwi-GUEST', '')
      
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.1)
      
    print(" Successful connection!")


def connect_mqtt_server():
    """
    Conecta ao servidor MQTT com as credenciais do HiveMQ,
    registra o callback de mensagens e assina o tópico de resposta.
    """
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

    # Registra a função que será chamada ao receber mensagens
    client.set_callback(on_message)
    client.connect()

    # Assina o tópico onde o HiveMQ envia a resposta
    client.subscribe(b"irrigacao/comando")
    print(". . .Successful connection!")
    print("Subscribed to [irrigacao/comando]")

    return client


def main():
    """
    Encapsulamento do fluxo padrão do sistema IoT.
    Os dados do sensor DHT22 são lidos a cada 10 segundos,
    enviados ao HiveMQ, e a resposta é aguardada via check_msg().
    """
    connect_wifi()
    mqtt_client = connect_mqtt_server()

    dht22 = dht.DHT22(Pin(5))

    last_temp = 0.0
    last_hum  = 0.0

    while True:
        try:
            dht22.measure()
            temp = dht22.temperature()
            hum  = dht22.humidity()

            message = "DHT22,id=100 temperature = {},humidity = {}".format(temp, hum)
            print("Envio de dados para Requisição :" + message)
            mqtt_client.publish(b"irrigacao/sensores", message)

            last_temp = temp
            last_hum  = hum

        except Exception as e:
            print("Erro na leitura ou envio dos dados :", e)

        # Verifica mensagens recebidas durante os 10 segundos de espera
        # check_msg() é não-bloqueante: retorna imediatamente se não há nada
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                mqtt_client.check_msg()  # Dispara on_message() se houver resposta
            except Exception as e:
                print("Error checking MQTT messages:", e)
            time.sleep(0.2)  # Pequena pausa para não sobrecarregar o loop


if __name__ == "__main__":
    main()