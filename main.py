import pygame
import requests
import math
import datetime
import socket
import time
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

# === Example Coordinates ===
latitude = 27.972538498010568
longitude = -82.53794988613856

# === Pygame Setup ===
pygame.init()
screen_width, screen_height = 240, 320
screen = pygame.display.set_mode((screen_width, screen_height))
hotspot_icon = pygame.image.load("hotspot-icon.png").convert_alpha()
hotspot_icon = pygame.transform.smoothscale(hotspot_icon, (30, 17))
print("Icon size:", hotspot_icon.get_size())
pygame.display.set_caption("picycle")

# Fonts
speed_font = pygame.font.SysFont(None, 120)     # Bigger for vertical layout
mph_font = pygame.font.SysFont(None, 40)        # Adjust MPH size accordingly
road_font_size = 40
road_font = pygame.font.SysFont(None, road_font_size)
time_font = pygame.font.SysFont(None, 28)       # Font for time display

clock = pygame.time.Clock()

# === Fetch Road Name ===
road_name = get_road_name(latitude, longitude)
cached_road_name = None
last_road_update_time = 0
update_interval_sec = 5

# Simulated speed
current_speed_mph = 35

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))  # Black background

    # === Draw current time at the top center (lowered to 30 pixels) ===
    now = datetime.datetime.now()
    connected = is_wifi_connected()

    current_time = time.time()
    if connected and current_time - last_road_update_time > update_interval_sec:
        try:
            road_name = get_road_name(latitude, longitude)
            cached_road_name = road_name
            last_road_update_time = current_time
        except Exception:
            road_name = cached_road_name if cached_road_name else "Unknown Road"
    else:
        road_name = cached_road_name if cached_road_name else "Unknown Road"

    if 'slide_y' not in locals():
        slide_y = 0
    target_y = 0 if connected else 100
    if slide_y < target_y:
        slide_y += (target_y - slide_y) * 0.1  # slower going down
    else:
        slide_y += (target_y - slide_y) * 0.3  # faster going up

    time_str = now.strftime("%I:%M %p").lstrip("0")
    time_surface = time_font.render(time_str, True, (255, 255, 255))
    combined_width = hotspot_icon.get_width() + 10 + time_surface.get_width()
    icon_x = (screen_width - combined_width) // 2
    icon_y = 30

    # Dim the icon if not connected
    icon_tinted = hotspot_icon.copy()
    if not connected:
        icon_tinted.fill((100, 100, 100, 255), special_flags=pygame.BLEND_RGBA_MULT)

    # Draw icon
    screen.blit(icon_tinted, (icon_x, icon_y))

    # Draw red slash if disconnected
    if not connected:
        pygame.draw.line(screen, (150, 0, 0), (icon_x, icon_y), (icon_x + 30, icon_y + 17), 2)

    # Draw time
    time_rect = time_surface.get_rect(topleft=(icon_x + hotspot_icon.get_width() + 5, icon_y))
    screen.blit(time_surface, time_rect)

    # Draw speed number and MPH label centered vertically and horizontally
    speed_surface = speed_font.render(str(current_speed_mph), True, (255, 255, 255))
    mph_surface = mph_font.render("MPH", True, (255, 255, 255))

    # Calculate combined height
    total_height = speed_surface.get_height() + 10 + mph_surface.get_height()  # 10 px gap

    # Start y so the block is centered roughly at 1/3 screen height
    start_y = screen_height // 3 - total_height // 2

    # Position speed
    speed_rect = speed_surface.get_rect(center=(screen_width // 2, start_y + speed_surface.get_height() // 1))
    screen.blit(speed_surface, speed_rect)

    # Position MPH below speed with 10 px padding
    mph_rect = mph_surface.get_rect(center=(screen_width // 2, speed_rect.bottom + 5 + mph_surface.get_height() // 2))
    screen.blit(mph_surface, mph_rect)

    # === Draw V-shaped gradient behind odometer ===
    v_height = 100 # Height of the V shape
    v_width_top = 60  # width of the V at the top (near speed)
    v_width_bottom = 200  # width at the bottom (behind odometer)

    # Center X
    cx = screen_width // 2

    # === Fake odometer display ===
    odometer_font = pygame.font.SysFont(None, 36)
    odometer_surface = odometer_font.render("12.9 mi", True, (255, 255, 255))
    odometer_rect = odometer_surface.get_rect(center=(screen_width // 2, mph_rect.bottom + 15 + odometer_surface.get_height() // 1.2))

    v_bottom_y = odometer_rect.centery + 33
    v_top_y = v_bottom_y - v_height

    v_surf = pygame.Surface((screen_width, v_height), pygame.SRCALPHA)

    for i in range(v_height):
        # Reduced alpha for subtle inner fill
        alpha = int(150 * (1 - i / v_height) * 0.3)  # 30% opacity max

        # Calculate horizontal width at this height (linear interpolation)
        line_width = v_width_bottom - (v_width_bottom - v_width_top) * (i / v_height)
        left_x = cx - line_width / 2
        right_x = cx + line_width / 2
        y = v_height - i - 1  # from bottom to top on surface

        # Draw horizontal line with reduced alpha (fill)
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (left_x, y), (right_x, y))

    # Draw left outline line with fading alpha
    for i in range(v_height):
        line_width = v_width_bottom - (v_width_bottom - v_width_top) * (i / v_height)
        left_x = int(cx - line_width / 2)
        y = v_height - i - 1
        alpha = int(200 * (1 - i / v_height))  # fade from 200 to 0
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (left_x, y), (left_x, y))

    # Draw right outline line with fading alpha
    for i in range(v_height):
        line_width = v_width_bottom - (v_width_bottom - v_width_top) * (i / v_height)
        right_x = int(cx + line_width / 2)
        y = v_height - i - 1
        alpha = int(200 * (1 - i / v_height))  # fade from 200 to 0
        pygame.draw.line(v_surf, (255, 255, 255, alpha), (right_x, y), (right_x, y))

    screen.blit(v_surf, (0, v_top_y + int(slide_y)))

    screen.blit(odometer_surface, odometer_rect)

    # Resize road name if too wide
    current_font_size = road_font_size
    road_font = pygame.font.SysFont(None, current_font_size)
    road_surface = road_font.render(road_name, True, (255, 255, 255))

    while road_surface.get_width() > screen_width - 40 and current_font_size > 12:
        current_font_size -= 2
        road_font = pygame.font.SysFont(None, current_font_size)
        road_surface = road_font.render(road_name, True, (255, 255, 255))

    # === Rounded corner gradient behind road section ===
    line_y = screen_height - 50 + int(slide_y)
    gradient_start = screen_height - 1 + int(slide_y)
    gradient_end = screen_height - 30 + int(slide_y)
    gradient_height = gradient_start - gradient_end
    for y in range(gradient_start, gradient_end - 1, -1):
        blend_y = (y - gradient_end) / gradient_height  # vertical blend 0 to 1
        for x in range(screen_width):
            dx = abs(x - screen_width // 2) / (screen_width // 2)
            corner_dip = 1 - 0.5 * dx**2  # smooth parabola shape
            final_blend = blend_y * corner_dip
            gray = int(0 + (160 * final_blend))  # From black to soft gray
            pygame.draw.line(screen, (gray, gray, gray), (x, y), (x, y))

    # Draw horizontal line near bottom, full width
    pygame.draw.line(screen, (255, 255, 255), (0, line_y), (screen_width, line_y), 3)

    # Draw road name centered below the line
    road_rect = road_surface.get_rect(center=(screen_width // 2, line_y + 25))
    screen.blit(road_surface, road_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
