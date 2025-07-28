import pygame
import requests
import math
import datetime
import socket
import time
import serial
import pynmea2

# === WiFi Connection Check ===
def is_wifi_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1)
        return True
    except OSError:
        return False

# === Reverse Geocoding Function ===
def get_road_name(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2"
    }
    headers = {
        "User-Agent": "PygameGPSApp/1.0 (contact@example.com)"
    }
    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
        road = data.get("address", {}).get("road", "Unknown Road")
        return road
    except Exception as e:
        return f"Error: {e}"

import serial

# Open serial port once globally
ser = serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=1)

latitude = None
longitude = None
current_speed_mph = 0
total_distance_miles = 0
last_gps_update_time = time.time()

pygame.init()
pygame.mouse.set_visible(False)

# Real screen is landscape 320x240
screen_width, screen_height = 320, 240
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)

# Portrait surface 240x320 to draw UI
portrait_width, portrait_height = 240, 320
portrait_surface = pygame.Surface((portrait_width, portrait_height))

hotspot_icon = pygame.image.load("hotspot-icon.png").convert_alpha()
hotspot_icon = pygame.transform.smoothscale(hotspot_icon, (30, 17))

pygame.display.set_caption("picycle")

speed_font = pygame.font.SysFont(None, 120)
mph_font = pygame.font.SysFont(None, 40)
road_font_size = 40
road_font = pygame.font.SysFont(None, road_font_size)
time_font = pygame.font.SysFont(None, 28)

clock = pygame.time.Clock()

cached_road_name = None
last_road_update_time = 0
last_latlon_print_time = 0
latlon_print_interval = 10  # seconds
update_interval_sec = 5

def read_gps():
    global latitude, longitude, current_speed_mph
    try:
        line = ser.readline().decode('ascii', errors='replace').strip()
        if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
            msg = pynmea2.parse(line)
            if msg.status == 'A':
                latitude = msg.latitude
                longitude = msg.longitude
                current_speed_mph = float(msg.spd_over_grnd) * 1.15078
                global total_distance_miles, last_gps_update_time
                current_time = time.time()
                time_delta = current_time - last_gps_update_time
                last_gps_update_time = current_time
                distance_traveled = (current_speed_mph * time_delta) / 3600.0  # mph * hours
                total_distance_miles += distance_traveled
    except Exception as e:
        print("GPS read error:", e)

running = True
slide_y = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    portrait_surface.fill((0, 0, 0))
    connected = is_wifi_connected()  # <--- Added this line

    old_latitude = latitude
    old_longitude = longitude
    old_speed = current_speed_mph

    read_gps()
    current_time = time.time()

    if (
        (latitude != old_latitude or longitude != old_longitude or current_speed_mph != old_speed)
        and latitude is not None and longitude is not None
    ):
        print(f"[GPS] Latitude: {latitude:.6f}, Longitude: {longitude:.6f}, Speed: {current_speed_mph:.2f} mph")

    # Print lat/lon and speed every 10 seconds regardless
    if latitude is not None and longitude is not None and current_time - last_latlon_print_time > latlon_print_interval:
        last_latlon_print_time = current_time

    # Update road name only if connected and enough time passed
    if connected and latitude and longitude and current_time - last_road_update_time > update_interval_sec:
        try:
            road_name = get_road_name(latitude, longitude)
            cached_road_name = road_name
            last_road_update_time = current_time
        except Exception as e:
            print("Reverse geocode error:", e)

    # rest of your drawing code goes here ...

    target_y = 0 if connected else 100
    if slide_y < target_y:
        slide_y += (target_y - slide_y) * 0.1
    else:
        slide_y += (target_y - slide_y) * 0.3

    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p").lstrip("0")
    time_surface = time_font.render(time_str, True, (255, 255, 255))
    combined_width = hotspot_icon.get_width() + 10 + time_surface.get_width()
    icon_x = (portrait_width - combined_width) // 2
    icon_y = 30

    icon_tinted = hotspot_icon.copy()
    if not connected:
        icon_tinted.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)

    portrait_surface.blit(icon_tinted, (icon_x, icon_y))

    if not connected:
        pygame.draw.line(portrait_surface, (150, 0, 0), (icon_x, icon_y), (icon_x + 30, icon_y + 17), 2)

    time_rect = time_surface.get_rect(topleft=(icon_x + hotspot_icon.get_width() + 5, icon_y))
    portrait_surface.blit(time_surface, time_rect)

    speed_surface = speed_font.render(f"{int(current_speed_mph)}", True, (255, 255, 255))
    mph_surface = mph_font.render("MPH", True, (255, 255, 255))

    total_height = speed_surface.get_height() + 10 + mph_surface.get_height()
    start_y = portrait_height // 3 - total_height // 2

    speed_rect = speed_surface.get_rect(center=(portrait_width // 2, start_y + speed_surface.get_height() // 1))
    portrait_surface.blit(speed_surface, speed_rect)

    mph_rect = mph_surface.get_rect(center=(portrait_width // 2, speed_rect.bottom + 5 + mph_surface.get_height() // 2))
    portrait_surface.blit(mph_surface, mph_rect)

    v_height = 100
    v_width_top = 60
    v_width_bottom = 200
    cx = portrait_width // 2
    odometer_font = pygame.font.SysFont(None, 36)
    odometer_surface = odometer_font.render(f"{total_distance_miles:.1f} mi", True, (255, 255, 255))
    odometer_rect = odometer_surface.get_rect(center=(portrait_width // 2, mph_rect.bottom + 15 + odometer_surface.get_height() // 1.2))

    v_bottom_y = odometer_rect.centery + 33
    v_top_y = v_bottom_y - v_height

    v_surf = pygame.Surface((portrait_width, v_height), pygame.SRCALPHA)
    for i in range(v_height):
        alpha = int(150 * (1 - i / v_height) * 0.3)
        line_width = v_width_bottom - (v_width_bottom - v_width_top) * (i / v_height)
        left_x = cx - line_width / 2
        right_x = cx + line_width / 2
        y = v_height - i - 1
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (left_x, y), (right_x, y))

    for i in range(v_height):
        line_width = v_width_bottom - (v_width_bottom - v_width_top) * (i / v_height)
        left_x = int(cx - line_width / 2)
        y = v_height - i - 1
        alpha = int(200 * (1 - i / v_height))
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (left_x, y), (left_x, y))
        right_x = int(cx + line_width / 2)
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (right_x, y), (right_x, y))

    portrait_surface.blit(v_surf, (0, v_top_y + int(slide_y)-10))
    portrait_surface.blit(odometer_surface, odometer_rect)

    # Get road name just before rendering it
    road_name = cached_road_name if cached_road_name else "Unknown Road"
    current_font_size = road_font_size
    road_font = pygame.font.SysFont(None, current_font_size)
    road_surface = road_font.render(road_name, True, (255, 255, 255))

    while road_surface.get_width() > portrait_width - 40 and current_font_size > 12:
        current_font_size -= 2
        road_font = pygame.font.SysFont(None, current_font_size)
        road_surface = road_font.render(road_name, True, (255, 255, 255))

    line_y = portrait_height - 50 + int(slide_y)
    gradient_start = portrait_height - 1 + int(slide_y)
    gradient_end = portrait_height - 30 + int(slide_y)
    gradient_height = gradient_start - gradient_end
    for y in range(gradient_start, gradient_end - 1, -1):
        blend_y = (y - gradient_end) / gradient_height
        for x in range(portrait_width):
            dx = abs(x - portrait_width // 2) / (portrait_width // 2)
            corner_dip = 1 - 0.5 * dx**2
            final_blend = blend_y * corner_dip
            gray = int(0 + (160 * final_blend))
            pygame.draw.line(portrait_surface, (gray, gray, gray), (x, y), (x, y))

    pygame.draw.line(portrait_surface, (255, 255, 255), (0, line_y), (portrait_width, line_y), 3)

    road_rect = road_surface.get_rect(center=(portrait_width // 2, line_y + 25))
    portrait_surface.blit(road_surface, road_rect)

    # Rotate portrait surface -90 deg and blit to landscape screen centered
    rotated_surface = pygame.transform.rotate(portrait_surface, -90)
    screen.fill((0, 0, 0))
    x = (screen_width - rotated_surface.get_width()) // 2
    y = (screen_height - rotated_surface.get_height()) // 2
    screen.blit(rotated_surface, (x, y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()