import serial
import pynmea2

# Open serial port to GPS module
serial_port = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=1)

print("Reading GPS data... (Press Ctrl+C to stop)")

try:
    while True:
        line = serial_port.readline().decode('ascii', errors='replace').strip()
        print(f"Raw line: {line}")  # Debug print

        if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
            try:
                msg = pynmea2.parse(line)
                if msg.status == 'A':  # 'A' means data is valid
                    lat = msg.latitude
                    lon = msg.longitude
                    speed_knots = float(msg.spd_over_grnd) if msg.spd_over_grnd else 0.0
                    speed_mph = speed_knots * 1.15078

                    print(f"Latitude: {lat:.6f}, Longitude: {lon:.6f}, Speed: {speed_mph:.1f} mph")
                else:
                    print("GPS data invalid")
            except pynmea2.ParseError as e:
                print(f"Parse error: {e}")
                continue
        else:
            print("Non-RMC sentence")

except KeyboardInterrupt:
    print("\nGPS reading stopped.")
finally:
    serial_port.close()