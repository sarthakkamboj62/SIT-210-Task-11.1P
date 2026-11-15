from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
from collections import deque
from threading import Lock
import math

app = Flask(__name__)

lock = Lock()

latest_data = {
    "temperature": None,
    "humidity": None,
    "light": None,
    "vibration": False,
    "status": "WAITING"
}

history = deque(maxlen=60)
vibration_count = 0
last_vibration = False
last_received = None


@app.route("/")
def dashboard():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Smart Beehive Monitoring</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            padding: 25px;
            font-family: Arial, sans-serif;
            background: #101827;
            color: #f8fafc;
        }

        header {
            max-width: 1200px;
            margin: auto auto 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        h1 { color: #fbbf24; margin-bottom: 5px; }

        .muted { color: #94a3b8; }

        .grid {
            max-width: 1200px;
            margin: auto;
            display: grid;
            grid-template-columns: repeat(
                auto-fit, minmax(220px, 1fr)
            );
            gap: 18px;
        }

        .card {
            background: #1e293b;
            padding: 22px;
            border-radius: 15px;
            border: 1px solid #334155;
        }

        .card h3 {
            color: #94a3b8;
            font-size: 15px;
        }

        .value {
            font-size: 32px;
            font-weight: bold;
            margin: 15px 0;
        }

        .unit {
            font-size: 15px;
            color: #94a3b8;
        }

        .section {
            max-width: 1200px;
            margin: 22px auto;
        }

        .graph {
            background: #1e293b;
            padding: 20px;
            border-radius: 15px;
            border: 1px solid #334155;
            margin-bottom: 18px;
        }

        canvas {
            width: 100%;
            height: 220px;
            display: block;
        }

        .status {
            padding: 17px;
            border-radius: 12px;
            text-align: center;
            font-weight: bold;
            margin: 20px auto;
            max-width: 1200px;
        }

        .normal { background: #14532d; color: #bbf7d0; }
        .warning { background: #713f12; color: #fef08a; }
        .critical { background: #7f1d1d; color: #fecaca; }
        .offline { background: #334155; color: #e2e8f0; }

        .online { color: #4ade80; }
        .offline-text { color: #f87171; }

        footer {
            text-align: center;
            color: #94a3b8;
            padding: 20px;
        }
    </style>
</head>

<body>

<header>
    <div>
        <h1>🐝 Smart Beehive Monitoring</h1>
        <div class="muted">Environmental Monitoring Dashboard</div>
    </div>

    <div>
        <strong id="connection">Checking connection...</strong>
    </div>
</header>

<div class="grid">

    <div class="card">
        <h3>🌡 Temperature</h3>
        <div class="value" id="temperature">-- <span class="unit">°C</span></div>
        <div class="muted">Live temperature</div>
    </div>

    <div class="card">
        <h3>💧 Humidity</h3>
        <div class="value" id="humidity">-- <span class="unit">%</span></div>
        <div class="muted">Live humidity</div>
    </div>

    <div class="card">
        <h3>☀ Light Intensity</h3>
        <div class="value" id="light">-- <span class="unit">lux</span></div>
        <div class="muted">Current light level</div>
    </div>

    <div class="card">
        <h3>📳 Vibration</h3>
        <div class="value" id="vibration">--</div>
        <div class="muted">Movement detection</div>
    </div>

    <div class="card">
        <h3>⚡ Vibration Events</h3>
        <div class="value" id="vibrationCount">0</div>
        <div class="muted">Events since server started</div>
    </div>

    <div class="card">
        <h3>📡 System Status</h3>
        <div class="value" id="systemStatus">WAITING</div>
        <div class="muted">Environmental condition</div>
    </div>

</div>

<div class="section">
    <div class="status offline" id="alertBox">
        Waiting for sensor data...
    </div>
</div>

<div class="section">

    <div class="graph">
        <h3>🌡 Temperature History</h3>
        <canvas id="temperatureChart"></canvas>
    </div>

    <div class="graph">
        <h3>💧 Humidity History</h3>
        <canvas id="humidityChart"></canvas>
    </div>

</div>

<footer>
    Last updated: <span id="updated">--</span>
    <br><br>
    Arduino Nano 33 IoT | Raspberry Pi 4 | HTTP Wi-Fi
</footer>

<script>
function drawGraph(canvasId, values, label, unit) {
    const canvas = document.getElementById(canvasId);
    const rect = canvas.getBoundingClientRect();

    const ratio = window.devicePixelRatio || 1;
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;

    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);

    const width = rect.width;
    const height = rect.height;

    ctx.clearRect(0, 0, width, height);

    const valid = values.filter(v => v !== null);

    if (valid.length < 2) {
        ctx.fillStyle = "#94a3b8";
        ctx.fillText("Waiting for readings...", 15, 30);
        return;
    }

    let min = Math.min(...valid);
    let max = Math.max(...valid);

    if (min === max) {
        min -= 1;
        max += 1;
    }

    const padding = 30;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1;

    for (let i = 0; i < 5; i++) {
        const y = padding + i * chartHeight / 4;

        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }

    ctx.strokeStyle = "#fbbf24";
    ctx.lineWidth = 2;
    ctx.beginPath();

    values.forEach((value, i) => {
        if (value === null) return;

        const x = padding +
            i * chartWidth / Math.max(values.length - 1, 1);

        const y = padding +
            (max - value) / (max - min) * chartHeight;

        if (i === 0 || values[i - 1] === null) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();

    ctx.fillStyle = "#f8fafc";
    ctx.font = "12px Arial";
    ctx.fillText(
        max.toFixed(1) + " " + unit,
        padding,
        15
    );
    ctx.fillText(
        min.toFixed(1) + " " + unit,
        padding,
        height - 5
    );
}

async function updateDashboard() {
    try {
        const response = await fetch("/api/latest");
        if (!response.ok) throw new Error("Server error");

        const data = await response.json();

        const online = data.online;

        document.getElementById("connection").textContent =
            online ? "● Arduino Online" : "● Arduino Offline";

        document.getElementById("connection").className =
            online ? "online" : "offline-text";

        document.getElementById("temperature").innerHTML =
            data.temperature === null ? "--" :
            Number(data.temperature).toFixed(1) +
            ' <span class="unit">°C</span>';

        document.getElementById("humidity").innerHTML =
            data.humidity === null ? "--" :
            Number(data.humidity).toFixed(1) +
            ' <span class="unit">%</span>';

        document.getElementById("light").innerHTML =
            data.light === null ? "--" :
            Number(data.light).toFixed(1) +
            ' <span class="unit">lux</span>';

        document.getElementById("vibration").textContent =
            data.vibration ? "DETECTED" : "NONE";

        document.getElementById("vibrationCount").textContent =
            data.vibration_count;

        document.getElementById("systemStatus").textContent =
            data.status;

        document.getElementById("updated").textContent =
            data.updated;

        const alertBox = document.getElementById("alertBox");

        alertBox.textContent = online ?
            "System condition: " + data.status :
            "WARNING: Arduino connection lost";

        alertBox.className = "status " +
            (!online ? "offline" :
            data.status === "NORMAL" ? "normal" :
            data.status === "WARNING" ? "warning" :
            "critical");

        drawGraph(
            "temperatureChart",
            data.history.map(x => x.temperature),
            "Temperature",
            "°C"
        );

        drawGraph(
            "humidityChart",
            data.history.map(x => x.humidity),
            "Humidity",
            "%"
        );

    } catch (error) {
        document.getElementById("connection").textContent =
            "● Server unavailable";
        document.getElementById("connection").className =
            "offline-text";
    }
}

updateDashboard();
setInterval(updateDashboard, 2000);

window.addEventListener("resize", updateDashboard);
</script>

</body>
</html>
    """)


@app.route("/api/sensors", methods=["POST"])
def receive_sensors():
    global latest_data, vibration_count
    global last_vibration, last_received

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        light = float(data["light"])
        vibration = data["vibration"]

        if not all(map(math.isfinite, [
            temperature, humidity, light
        ])):
            raise ValueError("Non-finite sensor reading")

        if not isinstance(vibration, bool):
            raise ValueError("Invalid vibration value")

        if not (-40 <= temperature <= 85):
            raise ValueError("Temperature out of range")

        if not (0 <= humidity <= 100):
            raise ValueError("Humidity out of range")

        if light < 0:
            raise ValueError("Invalid light reading")

    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Invalid sensor values"}), 400

    with lock:
        if vibration and not last_vibration:
            vibration_count += 1

        last_vibration = vibration

        if vibration or temperature > 35 or humidity < 30 or humidity > 80:
            status = "CRITICAL"
        elif temperature > 32 or humidity < 35 or humidity > 75:
            status = "WARNING"
        else:
            status = "NORMAL"

        latest_data = {
            "temperature": temperature,
            "humidity": humidity,
            "light": light,
            "vibration": vibration,
            "status": status
        }

        last_received = datetime.now()

        history.append({
            "temperature": temperature,
            "humidity": humidity,
            "time": last_received.strftime("%H:%M:%S")
        })

    print("Received:", latest_data)

    return jsonify({"message": "Data received"}), 200


@app.route("/api/latest")
def get_latest():

    with lock:
        online = (
            last_received is not None and
            (datetime.now() - last_received).total_seconds() < 10
        )

        result = dict(latest_data)
        result["online"] = online
        result["vibration_count"] = vibration_count
        result["updated"] = (
            last_received.strftime("%H:%M:%S")
            if last_received else "No data"
        )
        result["history"] = list(history)

    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"server": "running"})


if __name__ == "__main__":
    print("Smart Beehive Dashboard Starting...")
    app.run(host="0.0.0.0", port=5000, debug=False)
