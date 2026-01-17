"""
FIRST LEGO League "Unearthed" - Artifact Detector
Upload this to your LEGO Spike Prime via pybricks.com

Sensors:
- Ultrasonic Sensor (Port A): Proximity detector - detects objects on surface
- Color Sensor (Port B): "Material Analyzer" - identifies artifact type by color
  - Reflection % = signal strength (simulates how well we can "read" the material)

Communication Protocol:
- Sends JSON-formatted sensor data to web interface
- Receives commands from web interface

Artifact Types (by color):
- RED = Ancient pottery / ceramics
- YELLOW = Gold artifact
- GREEN = Copper/Bronze (oxidized)
- BLUE = Precious gems / lapis lazuli
- WHITE = Bone / ivory
- NONE = No artifact detected
"""
from pybricks.hubs import PrimeHub
from pybricks.pupdevices import UltrasonicSensor, ColorSensor
from pybricks.parameters import Port, Color
from pybricks.tools import wait, StopWatch
from usys import stdin
from uselect import poll

# Initialize hub and sensors
hub = PrimeHub()
radar = UltrasonicSensor(Port.A)  # "Ground penetrating radar"
analyzer = ColorSensor(Port.B)    # "Material analyzer"

# Set up stdin polling for receiving commands
p = poll()
p.register(stdin)

# Timers
heartbeat = StopWatch()
scan_timer = StopWatch()

# State
handshake_done = False
scanning = False
lights_on = False

# Artifact classification based on color
ARTIFACT_TYPES = {
    "RED": "Ancient Pottery",
    "YELLOW": "Gold Artifact", 
    "GREEN": "Bronze/Copper",
    "BLUE": "Precious Gems",
    "WHITE": "Bone/Ivory",
    "NONE": "No Detection"
}

def get_color_name(color):
    """Convert Color object to string name"""
    if color == Color.RED:
        return "RED"
    elif color == Color.YELLOW:
        return "YELLOW"
    elif color == Color.GREEN:
        return "GREEN"
    elif color == Color.BLUE:
        return "BLUE"
    elif color == Color.WHITE:
        return "WHITE"
    else:
        return "NONE"

def send_sensor_data():
    """Send current sensor readings as JSON"""
    distance = radar.distance()
    color = analyzer.color()
    color_name = get_color_name(color)
    hsv = analyzer.hsv()
    reflection = analyzer.reflection()
    
    # Determine if artifact detected:
    # - Ultrasonic detects something nearby (< 200mm)  
    # - OR color sensor has good reflection (> 10%) even if ultrasonic shows 2000
    # This helps when ultrasonic can't see through/around objects
    has_proximity = distance < 200
    has_reflection = reflection > 10
    artifact_detected = (has_proximity or has_reflection) and color_name != "NONE"
    artifact_type = ARTIFACT_TYPES.get(color_name, "Unknown")
    
    # Signal strength = reflection % (how well we can analyze the material)
    signal_strength = reflection
    
    # Send JSON data
    data = f'{{"dist":{distance},"signal":{signal_strength},"color":"{color_name}","artifact":"{artifact_type}","detected":{str(artifact_detected).lower()},"hsv":[{hsv.h},{hsv.s},{hsv.v}],"refl":{reflection}}}'
    print(f"data:{data}")
    
    return artifact_detected

def alert_artifact():
    """Visual/audio alert when artifact found"""
    hub.speaker.beep(frequency=1000, duration=100)
    hub.light.on(Color.GREEN)

def process_command(cmd):
    """Process commands from web interface"""
    global scanning, lights_on
    
    cmd = cmd.strip().lower()
    
    if cmd == "hello":
        return "hub: hello"
    elif cmd == "ping":
        return "hub: pong"
    elif cmd == "scan":
        # Single scan
        send_sensor_data()
        return "hub: scan complete"
    elif cmd == "start":
        # Start continuous scanning
        scanning = True
        hub.light.on(Color.BLUE)
        return "hub: scanning started"
    elif cmd == "stop":
        # Stop continuous scanning
        scanning = False
        hub.light.on(Color.WHITE)
        return "hub: scanning stopped"
    elif cmd == "beep":
        hub.speaker.beep()
        return "hub: beep"
    elif cmd == "light_on":
        lights_on = True
        radar.lights.on(100)
        analyzer.lights.on(100)
        return "hub: lights on"
    elif cmd == "light_off":
        lights_on = False
        radar.lights.off()
        analyzer.lights.off()
        return "hub: lights off"
    elif cmd == "light_toggle":
        lights_on = not lights_on
        if lights_on:
            radar.lights.on(100)
            analyzer.lights.on(100)
            return "hub: lights on"
        else:
            radar.lights.off()
            analyzer.lights.off()
            return "hub: lights off"
    elif cmd == "status":
        return f"hub: scanning={scanning},lights={lights_on}"
    else:
        return f"hub: unknown command '{cmd}'"

# Startup
print("boot")
hub.light.on(Color.ORANGE)

# Input buffer for building complete lines
input_buffer = ""

# Main loop
while True:
    # Before handshake: print "ready" every second
    if not handshake_done and heartbeat.time() >= 1000:
        print("ready")
        heartbeat.reset()
    
    # Continuous scanning mode: send data every 200ms
    if scanning and scan_timer.time() >= 200:
        artifact_found = send_sensor_data()
        if artifact_found:
            alert_artifact()
        scan_timer.reset()
    
    # Check for incoming data using poll
    while p.poll(0):
        # Read one character at a time
        char = stdin.read(1)
        if char:
            if char == '\n' or char == '\r':
                # Complete line received
                line = input_buffer.strip()
                input_buffer = ""
                if line:
                    response = process_command(line)
                    print(response)
                    
                    # Check for handshake
                    if line.lower() == "hello" and not handshake_done:
                        handshake_done = True
                        hub.light.on(Color.GREEN)
            else:
                input_buffer += char
        else:
            break
    
    wait(10)
