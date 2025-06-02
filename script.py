import pygame
import random
import sys
from PIL import Image
import time

clock = pygame.time.Clock()
FPS = 60
pygame.init()

# Ustawienia ekranu
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
# Wybór nazwy okna (np. z script.py, można zmienić)
pygame.display.set_caption("Car dziekanat")

# --- Zmiany dla Animacji Monety ---
COIN_SIZE = (40, 40)
coin_frames = []
try:
    gif_image = Image.open("coin.gif")
    if gif_image.n_frames > 0:  # Upewnij się, że GIF ma klatki
        for frame_num in range(gif_image.n_frames):
            gif_image.seek(frame_num)
            frame_rgba = gif_image.convert("RGBA")
            pygame_frame = pygame.image.fromstring(
                frame_rgba.tobytes(), frame_rgba.size, frame_rgba.mode
            )
            pygame_frame = pygame.transform.scale(pygame_frame, COIN_SIZE)
            pygame_frame = pygame_frame.convert_alpha()
            coin_frames.append(pygame_frame)
    else:
        print("Ostrzeżenie: coin.gif nie zawiera klatek animacji lub jest niepoprawny. Ładowanie jako statyczny obraz.")
        static_coin_img = pygame.image.load("coin.gif").convert_alpha()
        static_coin_img = pygame.transform.scale(static_coin_img, COIN_SIZE)
        coin_frames.append(static_coin_img)

except FileNotFoundError:
    print("Błąd: Nie znaleziono pliku coin.gif. Tworzenie zastępczej monety.")
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2), COIN_SIZE[0] // 2)
    coin_frames.append(fallback_coin_img)
except Exception as e:
    print(f"Błąd podczas ładowania coin.gif: {e}. Tworzenie zastępczej monety.")
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2), COIN_SIZE[0] // 2)
    coin_frames.append(fallback_coin_img)

if not coin_frames:
    print("Nie udało się załadować żadnych klatek monety. Tworzenie domyślnej.")
    fallback_coin_img = pygame.Surface(COIN_SIZE, pygame.SRCALPHA)
    pygame.draw.circle(fallback_coin_img, (255, 223, 0), (COIN_SIZE[0] // 2, COIN_SIZE[1] // 2),
                       COIN_SIZE[0] // 2)
    coin_frames.append(fallback_coin_img)

current_coin_frame_index = 0
coin_animation_timer = pygame.time.get_ticks()
COIN_ANIMATION_SPEED = 100
# --- Koniec Zmian dla Animacji Monety ---

coins = 0

# Kolory
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
BLUE = (100, 100, 255)

font = pygame.font.Font('munro.ttf', 18)
# Wybór subject_font (z script2.py dla lepszej czytelności)
subject_font = pygame.font.Font('munro.ttf', 22)


# Funkcje pomocnicze
def render_text_with_outline(font_obj, text, text_color, outline_color,
                             outline_thickness=1):
    text_width, text_height = font_obj.size(text)
    surface_size = (text_width + 2 * outline_thickness, text_height + 2 * outline_thickness)
    text_surface = pygame.Surface(surface_size, pygame.SRCALPHA)

    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx != 0 or dy != 0:
                text_outline = font_obj.render(text, True, outline_color)
                text_surface.blit(text_outline, (dx + outline_thickness, dy + outline_thickness))

    text_main = font_obj.render(text, True, text_color)
    text_surface.blit(text_main, (outline_thickness, outline_thickness))
    return text_surface


def get_clamped_text_rect(text_surface, pos):
    x, y = pos
    text_rect = text_surface.get_rect(center=(x + 30, y - 20))

    if text_rect.left < 0: text_rect.left = 0
    if text_rect.right > WIDTH: text_rect.right = WIDTH
    if text_rect.top < 0: text_rect.top = 0
    if text_rect.bottom > HEIGHT: text_rect.bottom = HEIGHT
    return text_rect


# Funkcja render_text_wrapped z script2.py
def render_text_wrapped(text_string, font_obj, text_color, max_width):
    words = text_string.split(' ')
    lines_text = []
    current_line_words = []

    for word in words:
        word_width = font_obj.size(word)[0]
        if not current_line_words and word_width > max_width:
            current_line_words.append(word)
            lines_text.append(" ".join(current_line_words))
            current_line_words = []
            continue
        temp_line_words = current_line_words + [word]
        temp_line = " ".join(temp_line_words)
        if font_obj.size(temp_line)[0] <= max_width:
            current_line_words.append(word)
        else:
            if current_line_words:
                lines_text.append(" ".join(current_line_words))
            current_line_words = [word]
            if word_width > max_width:
                lines_text.append(" ".join(current_line_words))
                current_line_words = []
    if current_line_words:
        lines_text.append(" ".join(current_line_words))
    surfaces = []
    total_height = 0
    line_spacing = 2
    for i, line_text in enumerate(lines_text):
        if line_text.strip():
            text_surf = font_obj.render(line_text, True, text_color)
            surfaces.append(text_surf)
            total_height += text_surf.get_height()
            if i < len(lines_text) - 1:
                total_height += line_spacing
    return surfaces, total_height


# Konfiguracja obiektów
# Używamy PE_SQUARES_2 z script2.py (zmieniona nazwa ostatniego elementu)
PE_SQUARES_2 = [
    {"rect": (200, 700, 50, 50), "message": "Siłownia"},
    {"rect": (350, 250, 50, 50), "message": "Ścianka wspinaczkowa"},
    {"rect": (1000, 450, 50, 50), "message": "Siatka"},
    {"rect": (1600, 400, 50, 50), "message": "Koszykówka"},
    {"rect": (1500, 920, 50, 50), "message": "Tenis stołowy"}
]

PAYMENTS_SQUARES = [
    {"rect": (250, 700, 50, 50), "message": "ECTS"},
    {"rect": (660, 700, 50, 50), "message": "Akademik"},
    {"rect": (1050, 690, 50, 50), "message": "Ubezpieczenie"},
    {"rect": (1550, 700, 50, 50), "message": "Legitymacja"}
]

GRADES_SQUARES = [
    {"rect": (1650, 780, 50, 50), "message": "Tablica ocen"}
]

START_POSITIONS = {
    "payments": (WIDTH // 2 - 50, HEIGHT - 150),
    "pe_enrollments": (WIDTH // 2 - 50, HEIGHT - 150),
    "grades": (WIDTH // 2 - 50, HEIGHT - 150)
}

# Grafiki
background = pygame.image.load("map.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("payments.png").convert()
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("PE_enrollment.png").convert()
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))
background3 = pygame.image.load("grades.png").convert()
background3 = pygame.transform.scale(background3, (WIDTH, HEIGHT))

# Maski kolizji
road_mask = pygame.image.load("map_mask.png").convert_alpha()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))
payments_mask = pygame.image.load("payments_mask.png").convert_alpha()
payments_mask = pygame.transform.scale(payments_mask, (WIDTH, HEIGHT))
pe_enrollment_mask = pygame.image.load("PE_enrollment_mask.png").convert_alpha()
pe_enrollment_mask = pygame.transform.scale(pe_enrollment_mask, (WIDTH, HEIGHT))
grades_mask = pygame.image.load("grades_mask.png").convert_alpha()
grades_mask = pygame.transform.scale(grades_mask, (WIDTH, HEIGHT))

# Postać i pojazd
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100
prawo_img = pygame.image.load("character_right.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("character_right_move.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("character_left.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("character_left_move.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

CAR_SIZE = (70, 70)
car_left = pygame.image.load("car_left.png").convert_alpha()
car_left = pygame.transform.scale(car_left, CAR_SIZE)
car_right = pygame.image.load("car_right.png").convert_alpha()
car_right = pygame.transform.scale(car_right, CAR_SIZE)
car_up = pygame.image.load("car_up.png").convert_alpha()
car_up = pygame.transform.scale(car_up, CAR_SIZE)
car_down = pygame.image.load("car_down.png").convert_alpha()
car_down = pygame.transform.scale(car_down, CAR_SIZE)

# Zmienne stanu
current_background = background
inside_building = False
entry_position = None
near_building = None
active_message = None
action_message = None
action_message_time = 0
show_grades = False
car_direction = "right"
car_x, car_y = 1000, 530
character_x, character_y = 350, 450

velocity_x_char, velocity_y_char = 0, 0
velocity_x_car, velocity_y_car = 0, 0
acceleration_char = 0.5
deceleration_char = 0.2
max_speed_char = 4
acceleration_car = 0.3
deceleration_car = 0.2
max_speed_car = 5

buildings = [(275, 20), (1800, 400), (1050, 650)]
facing = "prawo"
is_moving = False
animation_counter = 0
current_frame = 0

# System ocen
# Używamy listy subjects z script2.py dla testowania zawijania
subjects = [
    "podstawy /programowania", "analiza /matematyczna", "programowanie /obiektowe",
    "angielski", "Fizyka dla informatyków /i analityków danych"
]
grades = {
    subject: [random.randint(2, 5) for _ in range(random.randint(3, 5))]
    for subject in subjects
}

# Używamy wymiarów grades_bg z script2.py dla większej tablicy
grades_bg_width, grades_bg_height = 1015, 415
grades_bg_x = 455
grades_bg_y = 290
grades_bg = pygame.Surface((grades_bg_width, grades_bg_height))
grades_bg.fill((160, 82, 45))


def update_animation():
    global animation_counter, current_frame
    if is_moving:
        animation_counter += 1
        if animation_counter >= 10:
            animation_counter = 0
            current_frame = 1 - current_frame
    else:
        current_frame = 0


def get_player_image():
    if facing == "prawo":
        return prawo_idzie_img if current_frame == 1 else prawo_img
    return lewo_idzie_img if current_frame == 1 else lewo_img


LIGHT_GREEN_ALPHA = (144, 238, 144, 150)


def draw_interaction_indicators():
    indicator_radius = 25
    indicator_width = 3
    if inside_building:
        squares_to_draw = []
        if current_background == background1:
            squares_to_draw = PAYMENTS_SQUARES
        elif current_background == background2:
            squares_to_draw = PE_SQUARES_2  # Używamy zaktualizowanej listy
        elif current_background == background3:
            squares_to_draw = GRADES_SQUARES
        for sq_info in squares_to_draw:
            x, y, w, h = sq_info["rect"]
            center = (x + w // 2, y + h // 2)
            pygame.draw.circle(screen, LIGHT_GREEN_ALPHA, center, min(w, h) // 2 + 5, indicator_width)
    else:
        for bx, by in buildings:
            center_x = bx + CAR_SIZE[0] // 2
            center_y = by + CAR_SIZE[1] // 2
            pygame.draw.circle(screen, LIGHT_GREEN_ALPHA, (center_x, center_y), indicator_radius, indicator_width)


# Używamy handle_grades_display z script2.py (bardziej zaawansowana)
def handle_grades_display():
    grades_bg_rect = grades_bg.get_rect(topleft=(grades_bg_x, grades_bg_y))
    screen.blit(grades_bg, grades_bg_rect)
    pygame.draw.rect(screen, BLACK, grades_bg_rect, 2)
    y_offset = grades_bg_rect.y + 25
    x_start = grades_bg_rect.x + 25
    max_subject_width = grades_bg_width * 0.48
    spacing_after_subject = 40
    grade_spacing = 38
    vertical_spacing_between_subjects = 20
    line_spacing_for_wrapped_subject = 2
    for subject, grades_list in grades.items():
        original_y_for_this_subject_entry = y_offset
        subject_parts = subject.split('/')
        current_render_y = y_offset
        total_rendered_subject_height = 0
        for part_idx, part_text in enumerate(subject_parts):
            part_text = part_text.strip()
            rendered_lines_surfaces, part_block_height = render_text_wrapped(part_text, subject_font, BLACK,
                                                                             max_subject_width)
            temp_y = current_render_y
            for line_surf in rendered_lines_surfaces:
                screen.blit(line_surf, (x_start, temp_y))
                temp_y += line_surf.get_height() + line_spacing_for_wrapped_subject
            current_render_y = temp_y
            if rendered_lines_surfaces:
                current_render_y -= line_spacing_for_wrapped_subject
            total_rendered_subject_height = current_render_y - original_y_for_this_subject_entry
        grade_x = x_start + max_subject_width + spacing_after_subject
        example_grade_surf_height = subject_font.size("5")[1]
        grades_vertical_center_y = original_y_for_this_subject_entry + (
                    total_rendered_subject_height - example_grade_surf_height) // 2
        if total_rendered_subject_height == 0 and subject_parts:
            grades_vertical_center_y = original_y_for_this_subject_entry + (
                        subject_font.get_height() - example_grade_surf_height) // 2
        for grade_val in grades_list:
            color = GREEN if grade_val >= 3 else RED
            grade_text_surf = subject_font.render(str(grade_val), True, color)
            screen.blit(grade_text_surf, (grade_x, grades_vertical_center_y))
            grade_x += grade_spacing
        y_offset = current_render_y + vertical_spacing_between_subjects
        if total_rendered_subject_height == 0 and subject_parts:
            y_offset = original_y_for_this_subject_entry + subject_font.get_height() + vertical_spacing_between_subjects


# --- Logika monet ---
# Używamy dynamicznego spawnowania monet z script2.py
active_coins = []
MAX_ACTIVE_COINS = 10
COIN_SPAWN_INTERVAL = 5000
last_coin_spawn_time = pygame.time.get_ticks()

coin_spawn_cooldowns = {}
COIN_SPOT_COOLDOWN_DURATION = 15000
MAX_SPAWN_ATTEMPTS = 50  # Z script2.py
last_cooldown_cleanup_time = pygame.time.get_ticks()


def get_random_coin_spawn_position():  # Z script2.py
    rand_x = random.randint(0, WIDTH - COIN_SIZE[0])
    rand_y = random.randint(0, HEIGHT - COIN_SIZE[1])
    return (rand_x, rand_y)


def spawn_coin():  # Zmodyfikowana wersja z script2.py
    global active_coins, coin_spawn_cooldowns  # Dodano coin_spawn_cooldowns
    current_time_ticks = pygame.time.get_ticks()
    if len(active_coins) < MAX_ACTIVE_COINS:
        for _ in range(MAX_SPAWN_ATTEMPTS):
            potential_pos = get_random_coin_spawn_position()
            if potential_pos in active_coins:
                continue
            if potential_pos in coin_spawn_cooldowns and current_time_ticks < coin_spawn_cooldowns[potential_pos]:
                continue
            coin_img_for_check = coin_frames[0]
            check_x = potential_pos[0] + coin_img_for_check.get_width() // 2
            check_y = potential_pos[1] + coin_img_for_check.get_height() // 2
            is_on_road = False
            if 0 <= check_x < WIDTH and 0 <= check_y < HEIGHT:
                try:
                    if road_mask.get_at((check_x, check_y))[0:3] == (255, 255, 255):
                        is_on_road = True
                except IndexError:
                    pass
            if is_on_road:
                active_coins.append(potential_pos)
                coin_spawn_cooldowns[potential_pos] = current_time_ticks + COIN_SPOT_COOLDOWN_DURATION
                return


# --- Koniec logiki monet ---

# --- Menu startowe/pauzy (z script.py) ---
try:
    gear_icon_original = pygame.image.load("gear.png").convert_alpha()
    GEAR_ICON_SIZE = (100, 100)
    gear_icon = pygame.transform.scale(gear_icon_original, GEAR_ICON_SIZE)
    gear_icon_rect = gear_icon.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
except pygame.error as e:
    print(f"Ostrzeżenie: Nie udało się załadować gear.png: {e}. Ikona ustawień nie będzie dostępna.")
    gear_icon = None
    gear_icon_rect = None


def start_screen(is_pause_menu=False):
    title_font = pygame.font.Font('munro.ttf', 100)
    button_font = pygame.font.Font('munro.ttf', 50)
    title_text_content = "Ustawienia" if is_pause_menu else "Car Dziekanat"  # Zgodnie z script.py
    start_button_text_content = "Wznów" if is_pause_menu else "Start"
    button_width = 300
    button_height = 80
    start_button = pygame.Rect(WIDTH / 2 - button_width / 2, HEIGHT / 2 - button_height / 2 - 50, button_width,
                               button_height)
    exit_button = pygame.Rect(WIDTH / 2 - button_width / 2, HEIGHT / 2 + button_height / 2 + 10, button_width,
                              button_height)
    dim_overlay = None
    if is_pause_menu:
        dim_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Zamiast screen.blit(current_background, (0,0)) tutaj,
        # lepiej polegać na tym, że główna pętla już narysowała klatkę gry.
        # Można dodać dim_overlay.fill((0,0,0,180)) jeśli chcemy ciemniejsze tło.
    menu_running = True
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()
        if is_pause_menu and dim_overlay:
            # Rysujemy klatkę gry pod menu pauzy, jeśli jeszcze nie była narysowana
            # lub jeśli chcemy efekt przyciemnienia na statycznym tle.
            # Dla uproszczenia, polegamy na tym, że klatka gry jest już na ekranie.
            # Można by tu skopiować aktualny screen do dim_overlay i przyciemnić.
            pass  # Założenie: główna pętla narysowała tło
        elif not is_pause_menu:
            screen.blit(current_background, (0, 0))

        if is_pause_menu:  # Dodatkowe przyciemnienie dla menu pauzy
            overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 150))  # Ciemne, półprzezroczyste
            screen.blit(current_background, (0, 0))

        title_surf = render_text_with_outline(title_font, title_text_content, WHITE, BLACK, 3)
        title_rect = title_surf.get_rect(center=(WIDTH / 2, HEIGHT / 4))
        screen.blit(title_surf, title_rect)
        start_color = BLUE if start_button.collidepoint(mouse_pos) else (0, 0, 180)
        exit_color = RED if exit_button.collidepoint(mouse_pos) else (180, 0, 0)
        pygame.draw.rect(screen, start_color, start_button, border_radius=15)
        pygame.draw.rect(screen, exit_color, exit_button, border_radius=15)
        start_text_surf = button_font.render(start_button_text_content, True, WHITE)
        exit_text_surf = button_font.render("Wyjdź", True, WHITE)
        screen.blit(start_text_surf, start_text_surf.get_rect(center=start_button.center))
        screen.blit(exit_text_surf, exit_text_surf.get_rect(center=exit_button.center))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if start_button.collidepoint(event.pos):
                        menu_running = False
                    if exit_button.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and is_pause_menu:
                    menu_running = False
        pygame.display.flip()
        clock.tick(FPS)


# Wywołanie ekranu startowego na początku gry
start_screen(is_pause_menu=False)
# --- Koniec Menu ---

running = True
while running:
    current_time = pygame.time.get_ticks()
    active_message = None

    if pygame.time.get_ticks() - coin_animation_timer > COIN_ANIMATION_SPEED:
        current_coin_frame_index = (current_coin_frame_index + 1) % len(coin_frames)
        coin_animation_timer = pygame.time.get_ticks()
    active_coin_image = coin_frames[current_coin_frame_index]

    screen.blit(current_background, (0, 0))

    coins_text_surf = font.render(f"{coins}", True, BLACK)
    coins_text_rect = coins_text_surf.get_rect(topright=(WIDTH - 10, 10))
    screen.blit(coins_text_surf, coins_text_rect)
    coin_display_rect = active_coin_image.get_rect(topright=(
        coins_text_rect.left - 5, coins_text_rect.top + (coins_text_rect.height - active_coin_image.get_height()) // 2))
    screen.blit(active_coin_image, coin_display_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:  # Z script.py
            if event.button == 1:
                if gear_icon and gear_icon_rect and gear_icon_rect.collidepoint(event.pos):
                    # Przed wywołaniem menu pauzy, "zapisz" aktualny ekran, aby go wyświetlić pod spodem
                    # To jest uproszczenie; idealnie byłoby skopiować screen surface
                    # screen.blit(screen, (0,0)) # Nie jest to najlepsza praktyka tutaj
                    start_screen(is_pause_menu=True)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and inside_building:
                inside_building = False
                show_grades = False
                current_background = background
                if entry_position:
                    car_x, car_y = entry_position
                velocity_x_char, velocity_y_char = 0, 0
            elif event.key == pygame.K_e:
                player_rect_center_x = character_x + PLAYER_WIDTH // 2
                player_rect_center_y = character_y + PLAYER_HEIGHT // 2
                player_interaction_rect = pygame.Rect(player_rect_center_x - 10, player_rect_center_y - 10, 20, 20)
                if inside_building:
                    target_squares = []
                    if current_background == background1:
                        target_squares = PAYMENTS_SQUARES
                    elif current_background == background2:
                        target_squares = PE_SQUARES_2
                    elif current_background == background3:
                        target_squares = GRADES_SQUARES
                    for sq_info in target_squares:
                        sq_rect = pygame.Rect(sq_info["rect"])
                        if player_interaction_rect.colliderect(sq_rect):
                            if current_background == background3 and sq_info["message"] == "Tablica ocen":
                                show_grades = not show_grades
                                action_message = "Oceny " + ("pokazane" if show_grades else "ukryte")
                            else:
                                action_message = f"{sq_info['message']}: Akcja!"
                            action_message_time = current_time
                            break
                elif near_building:
                    inside_building = True
                    entry_position = (car_x, car_y)
                    if near_building == buildings[0]:
                        current_background = background1
                        character_x, character_y = START_POSITIONS["payments"]
                    elif near_building == buildings[1]:
                        current_background = background2
                        character_x, character_y = START_POSITIONS["pe_enrollments"]
                    elif near_building == buildings[2]:
                        current_background = background3
                        character_x, character_y = START_POSITIONS["grades"]
                    velocity_x_car, velocity_y_car = 0, 0
                    is_moving = False
                    current_frame = 0

    keys = pygame.key.get_pressed()

    if inside_building:
        new_velocity_x_char, new_velocity_y_char = velocity_x_char, velocity_y_char
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_velocity_x_char = max(-max_speed_char, new_velocity_x_char - acceleration_char)
            facing = "lewo"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_velocity_x_char = min(max_speed_char, new_velocity_x_char + acceleration_char)
            facing = "prawo"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_velocity_y_char = max(-max_speed_char, new_velocity_y_char - acceleration_char)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_velocity_y_char = min(max_speed_char, new_velocity_y_char + acceleration_char)

        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if new_velocity_x_char > 0:
                new_velocity_x_char = max(0, new_velocity_x_char - deceleration_char)
            elif new_velocity_x_char < 0:
                new_velocity_x_char = min(0, new_velocity_x_char + deceleration_char)
        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
            if new_velocity_y_char > 0:
                new_velocity_y_char = max(0, new_velocity_y_char - deceleration_char)
            elif new_velocity_y_char < 0:
                new_velocity_y_char = min(0, new_velocity_y_char + deceleration_char)

        velocity_x_char, velocity_y_char = new_velocity_x_char, new_velocity_y_char
        is_moving = abs(velocity_x_char) > 0.1 or abs(velocity_y_char) > 0.1
        prev_char_x, prev_char_y = character_x, character_y
        character_x += velocity_x_char
        character_y += velocity_y_char

        mask_to_check = None
        if current_background == background1:
            mask_to_check = payments_mask
        elif current_background == background2:
            mask_to_check = pe_enrollment_mask
        elif current_background == background3:
            mask_to_check = grades_mask

        if mask_to_check:
            player_points_to_check = [
                (int(character_x + PLAYER_WIDTH * 0.25), int(character_y + PLAYER_HEIGHT * 0.9)),
                (int(character_x + PLAYER_WIDTH * 0.75), int(character_y + PLAYER_HEIGHT * 0.9)),
                (int(character_x + PLAYER_WIDTH * 0.5), int(character_y + PLAYER_HEIGHT * 0.95))
            ]
            collision_detected = False
            for p_x, p_y in player_points_to_check:
                if not (0 <= p_x < WIDTH and 0 <= p_y < HEIGHT) or \
                        mask_to_check.get_at((p_x, p_y))[0:3] != (255, 255, 255):
                    collision_detected = True
                    break
            if collision_detected:
                character_x, character_y = prev_char_x, prev_char_y
                velocity_x_char, velocity_y_char = 0, 0

        character_x = max(0, min(character_x, WIDTH - PLAYER_WIDTH))
        character_y = max(0, min(character_y, HEIGHT - PLAYER_HEIGHT))
        update_animation()
        screen.blit(get_player_image(), (character_x, character_y))
        if current_background == background3 and show_grades:
            handle_grades_display()

        player_rect_center_x = character_x + PLAYER_WIDTH // 2
        player_rect_center_y = character_y + PLAYER_HEIGHT // 2
        player_interaction_rect = pygame.Rect(player_rect_center_x - 5, player_rect_center_y - 5, 10, 10)
        target_squares_for_msg = []
        if current_background == background1:
            target_squares_for_msg = PAYMENTS_SQUARES
        elif current_background == background2:
            target_squares_for_msg = PE_SQUARES_2
        elif current_background == background3:
            target_squares_for_msg = GRADES_SQUARES
        for sq_info in target_squares_for_msg:
            if player_interaction_rect.colliderect(pygame.Rect(sq_info["rect"])):
                active_message = sq_info["message"]
                break
    else:  # Poza budynkiem
        new_car_direction = car_direction
        new_velocity_x_car, new_velocity_y_car = velocity_x_car, velocity_y_car
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_velocity_x_car = max(-max_speed_car, new_velocity_x_car - acceleration_car)
            new_car_direction = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_velocity_x_car = min(max_speed_car, new_velocity_x_car + acceleration_car)
            new_car_direction = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_velocity_y_car = max(-max_speed_car, new_velocity_y_car - acceleration_car)
            new_car_direction = "up"
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_velocity_y_car = min(max_speed_car, new_velocity_y_car + acceleration_car)
            new_car_direction = "down"

        if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d]):
            if new_velocity_x_car > 0:
                new_velocity_x_car = max(0, new_velocity_x_car - deceleration_car)
            elif new_velocity_x_car < 0:
                new_velocity_x_car = min(0, new_velocity_x_car + deceleration_car)
        if not (keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_DOWN] or keys[pygame.K_s]):
            if new_velocity_y_car > 0:
                new_velocity_y_car = max(0, new_velocity_y_car - deceleration_car)
            elif new_velocity_y_car < 0:
                new_velocity_y_car = min(0, new_velocity_y_car + deceleration_car)

        car_direction = new_car_direction
        velocity_x_car, velocity_y_car = new_velocity_x_car, new_velocity_y_car
        prev_car_x, prev_car_y = car_x, car_y
        car_x += velocity_x_car
        car_y += velocity_y_car

        car_center_x = int(car_x + CAR_SIZE[0] // 2)
        car_center_y = int(car_y + CAR_SIZE[1] // 2)
        if not (0 <= car_center_x < WIDTH and 0 <= car_center_y < HEIGHT) or \
                road_mask.get_at((car_center_x, car_center_y))[0:3] != (255, 255, 255):
            car_x, car_y = prev_car_x, prev_car_y
            velocity_x_car, velocity_y_car = 0, 0

        car_x = max(0, min(car_x, WIDTH - CAR_SIZE[0]))
        car_y = max(0, min(car_y, HEIGHT - CAR_SIZE[1]))

        near_building = None
        car_rect_check = pygame.Rect(car_x, car_y, CAR_SIZE[0], CAR_SIZE[1])
        for b_idx, (bx, by) in enumerate(buildings):
            building_entry_rect = pygame.Rect(bx, by, 50, 50)
            if car_rect_check.colliderect(building_entry_rect):
                near_building = (bx, by)
                break
        car_image_to_blit = {"left": car_left, "right": car_right, "up": car_up, "down": car_down}[car_direction]
        screen.blit(car_image_to_blit, (car_x, car_y))
        if near_building:
            text_surf = render_text_with_outline(font, "Wciśnij E", BLACK, YELLOW)
            text_rect_clamped = get_clamped_text_rect(text_surf, (car_x, car_y))
            screen.blit(text_surf, text_rect_clamped)

        if current_time - last_coin_spawn_time > COIN_SPAWN_INTERVAL:
            spawn_coin()
            last_coin_spawn_time = current_time

        if current_time - last_cooldown_cleanup_time > 30000:  # Z script2.py
            expired_keys = [pos for pos, expiry_time in coin_spawn_cooldowns.items() if current_time >= expiry_time]
            for key in expired_keys:
                del coin_spawn_cooldowns[key]
            last_cooldown_cleanup_time = current_time

        car_collision_rect = pygame.Rect(car_x, car_y, CAR_SIZE[0], CAR_SIZE[1])
        coins_to_remove = []
        for coin_p in active_coins:  # Iteracja po liście, która może być modyfikowana
            coin_on_map_rect = active_coin_image.get_rect(topleft=coin_p)
            screen.blit(active_coin_image, coin_on_map_rect)
            if car_collision_rect.colliderect(coin_on_map_rect):
                coins_to_remove.append(coin_p)
                coins += 1

        for collected_coin_pos in coins_to_remove:
            if collected_coin_pos in active_coins:
                active_coins.remove(collected_coin_pos)

    draw_interaction_indicators()

    if active_message:
        text_surf = render_text_with_outline(font, active_message, BLACK, YELLOW)
        text_pos_x = character_x + PLAYER_WIDTH // 2
        text_pos_y = character_y - 10
        text_rect_clamped = get_clamped_text_rect(text_surf, (text_pos_x - 30, text_pos_y + 20))
        screen.blit(text_surf, text_rect_clamped)

    if action_message and (current_time - action_message_time) < 2000:
        text_surf = render_text_with_outline(font, action_message, BLACK, YELLOW, 2)
        text_rect = text_surf.get_rect(center=(WIDTH // 2, 50))
        screen.blit(text_surf, text_rect)
    elif action_message and (current_time - action_message_time) >= 2000:
        action_message = None

    if gear_icon and gear_icon_rect:  # Z script.py
        screen.blit(gear_icon, gear_icon_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()