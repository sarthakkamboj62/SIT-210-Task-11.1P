# Smart Beehive Monitoring System

## Project Overview
The Smart Beehive Monitoring System monitors environmental conditions inside a beehive using an Arduino Nano 33 IoT and Raspberry Pi 4.

## Hardware Components
- Arduino Nano 33 IoT
- Raspberry Pi 4
- DHT22 Temperature and Humidity Sensor
- BH1750 Light Sensor
- SW-420 Vibration Sensor
- Green LED
- Red LED

## Technologies Used
- Arduino C++
- Python
- Flask
- HTTP Communication
- Wi-Fi
- HTML, CSS and JavaScript

## Project Structure
- Arduino: Sensor readings, alert detection and HTTP data transmission.
- RaspberryPi: Flask server, live dashboard and sensor data processing.

## Features
- Live temperature monitoring
- Humidity monitoring
- Light intensity monitoring
- Vibration detection
- Vibration event counter
- Temperature and humidity history graphs
- Normal and alert status indicators
- LED-based alerts

## Installation

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the Raspberry Pi server:

```bash
python3 app.py
```

The dashboard runs on port 5000.

## Communication
The Arduino sends sensor readings to the Raspberry Pi using HTTP POST requests over Wi-Fi.
