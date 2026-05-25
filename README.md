# ESP32 — Firmware de Irrigação IoT

Firmware MicroPython para ESP32-C3 que coleta dados de temperatura e umidade via sensor DHT22 e os publica no broker MQTT HiveMQ Cloud. Com base nas leituras, o sistema recebe comandos de irrigação (`ON`/`OFF`) e aciona LEDs de feedback visual.

## Visão Geral

```
DHT22 (pino 5)
      │
      ▼
  ESP32-C3  ──── Wi-Fi ────► HiveMQ Cloud
      │                           │
      │        irrigacao/sensores │ (publish)
      │        irrigacao/comando  │ (subscribe)
      │                           │
      ▼
  LED Verde (pino 2) → irrigação ATIVADA
  LED Vermelho (pino 4) → irrigação DESATIVADA
```

## Hardware

| Componente        | Pino ESP32-C3 | Observação              |
|-------------------|---------------|-------------------------|
| DHT22 (DATA)      | GPIO 5        | VCC = 3.3V              |
| LED Verde (anodo) | GPIO 2        | Resistor 220Ω em série  |
| LED Vermelho (anodo) | GPIO 4     | Resistor 220Ω em série  |

## Tópicos MQTT

| Tópico               | Direção   | Formato (payload)                              |
|----------------------|-----------|------------------------------------------------|
| `irrigacao/sensores` | Publish   | `DHT22,id=100 temperature=XX.X,humidity=XX.X` |
| `irrigacao/comando`  | Subscribe | `ON` ou `OFF`                                  |

O payload de sensores segue o formato **InfluxDB Line Protocol**, compatível com a ingestão direta pelo backend do FieldHub.

## Comportamento dos LEDs

| Mensagem recebida | LED Verde | LED Vermelho | Duração |
|-------------------|-----------|--------------|---------|
| `ON`              | Aceso     | Apagado      | 3 s     |
| `OFF`             | Apagado   | Aceso        | 3 s     |
| Desconhecido      | Pisca     | Pisca        | 3× 0.3s |

## Broker MQTT (HiveMQ Cloud)

- **Host:** `420fea555ede4bd4a100b1da5ef2a840.s1.eu.hivemq.cloud`
- **Porta:** `8883` (TLS)
- **Usuário:** `fieldhub`
- **Client ID:** `100`

> Para uso em produção (hardware físico), substitua as credenciais por variáveis de ambiente ou um arquivo de configuração separado.

## Equipe

| Nome |
|------|
| Gabriel Nunes Rodrigues
| Alexander Da Silva Fernandes
| Lucas Panebianchi Antunes 
| Moisés Ivanildo Ferreira
| Maria Eduarda Fernandes Filhik  

---

## Simulação Wokwi

O arquivo `diagram.json` contém o circuito completo para simulação no [Wokwi](https://wokwi.com).  
Projeto original: https://wokwi.com/projects/464847397640316929
