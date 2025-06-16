import pygame
import random
import sys
from PIL import Image
import time
# === NOWE IMPORTY ===
import socket
import pickle


# ====================

# === NOWA KLASA SIECIOWA (z client_modified_v2.py) ===
class Network:
    def __init__(self, server_host, server_port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_host, server_port)
        self.player_id = None
        self.initial_player_state = None

    def connect(self):
        try:
            print(f"[ŁĄCZENIE] Próba połączenia z serwerem {self.server_address}...")
            self.client_socket.connect(self.server_address)
            initial_data_payload = self.client_socket.recv(4096)
            if not initial_data_payload:
                print("[BŁĄD POŁĄCZENIA] Nie otrzymano danych początkowych od serwera.")
                return None
            initial_data = pickle.loads(initial_data_payload)
            self.player_id = initial_data.get("id")
            self.initial_player_state = initial_data.get("initial_state")
            print(f"[POŁĄCZONO] Pomyślnie połączono z serwerem. Twoje ID: {self.player_id}")
            return self.initial_player_state
        except socket.error as e:
            print(f"[BŁĄD POŁĄCZENIA] Nie udało się połączyć z serwerem {self.server_address}: {e}")
            return None
        except (pickle.PickleError, EOFError) as e:
            print(f"[BŁĄD DANYCH POCZĄTKOWYCH] {e}")
            return None

    def send(self, data):
        try:
            self.client_socket.send(pickle.dumps(data))
            response_payload = self.client_socket.recv(4096)
            if not response_payload:
                return None
            return pickle.loads(response_payload)
        except socket.error:
            return None
        except pickle.PickleError:
            return None

    def close(self):
        self.client_socket.close()


# =======================================================


clock = pygame.time.Clock()
FPS = 60
pygame.init()

# Ustawienia ekranu
WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car dziekanat - Klient Sieciowy")

COIN_SIZE = (40, 40)
coin_frames = []
try:
    gif_image = Image.open("graphics icons/coin.gif")
    if gif_image.n_frames > 0:
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
GREY = (128, 128, 128)
TASK_BOARD_BG_COLOR = (50, 50, 50, 180)

font = pygame.font.Font('fonts/munro.ttf', 18)
subject_font = pygame.font.Font('fonts/munro.ttf', 22)
task_font = pygame.font.Font('fonts/munro.ttf', 20)
garage_font = pygame.font.Font('fonts/munro.ttf', 30)

# --- Logika zadań ---
TASK_ICON_SIZE = (25, 25)
LINE_SPACING_INSIDE_TASK = 2  # Odstęp między liniami wewnątrz jednego zadania
try:
    check_mark_img_orig = pygame.image.load("graphics icons/check_mark.png").convert_alpha()
    check_mark_img = pygame.transform.scale(check_mark_img_orig, TASK_ICON_SIZE)
except FileNotFoundError:
    print("Ostrzeżenie: Nie znaleziono pliku chec_mark.png. Tworzenie zastępczego.")
    check_mark_img = pygame.Surface(TASK_ICON_SIZE, pygame.SRCALPHA)
    pygame.draw.line(check_mark_img, GREEN, (5, TASK_ICON_SIZE[1] // 2),
                     (TASK_ICON_SIZE[0] // 2, TASK_ICON_SIZE[1] - 5), 3)
    pygame.draw.line(check_mark_img, GREEN, (TASK_ICON_SIZE[0] // 2, TASK_ICON_SIZE[1] - 5), (TASK_ICON_SIZE[0] - 5, 5),
                     3)

try:
    cross_mark_img_orig = pygame.image.load("graphics icons/cross_mark.png").convert_alpha()
    cross_mark_img = pygame.transform.scale(cross_mark_img_orig, TASK_ICON_SIZE)
except FileNotFoundError:
    print("Ostrzeżenie: Nie znaleziono pliku cross_mark.png. Tworzenie zastępczego.")
    cross_mark_img = pygame.Surface(TASK_ICON_SIZE, pygame.SRCALPHA)
    pygame.draw.line(cross_mark_img, RED, (5, 5), (TASK_ICON_SIZE[0] - 5, TASK_ICON_SIZE[1] - 5), 3)
    pygame.draw.line(cross_mark_img, RED, (5, TASK_ICON_SIZE[1] - 5), (TASK_ICON_SIZE[0] - 5, 5), 3)

task_pool_1 = [
    {"text": "Zapisz się na siłownię w klubie osiedlowym", "id": "Siłownia"},
    {"text": "Zapisz się na ściankę wspinaczkową 'Pod Chmurką'", "id": "Ścianka wspinaczkowa"},
    {"text": "Zapisz się na siatkówkę plażową - nabór otwarty", "id": "Siatka"},
    {"text": "Zapisz się na koszykówkę do drużyny 'Orły'", "id": "Koszykówka"},
    {"text": "Zapisz się na tenis stołowy - sekcja dla amatorów", "id": "Tenis stołowy"}
]

task_pool_2 = [
    {"text": "Zapłać za Punkty ECTS - termin mija jutro!", "id": "ECTS"},
    {"text": "Zapłać za akademik - pokój numer 305", "id": "Akademik"},
    {"text": "Zapłać za ubezpieczenie studenckie NNW", "id": "Ubezpieczenie"},
    {"text": "Zapłać za nową legitymację studencką", "id": "Legitymacja"}
]

current_tasks = []


def generate_tasks():
    global current_tasks
    current_tasks = []

    current_tasks.append({"text": "Sprawdź swoje najnowsze oceny w systemie", "id": "Tablica ocen", "completed": False})

    if task_pool_1:
        task1_data = random.choice(task_pool_1)
        current_tasks.append({"text": task1_data["text"], "id": task1_data["id"], "completed": False})
    else:
        current_tasks.append({"text": "Brak zadań sportowych", "id": "fallback_pool1", "completed": False})

    if task_pool_2:
        task2_data = random.choice(task_pool_2)
        current_tasks.append({"text": task2_data["text"], "id": task2_data["id"], "completed": False})
    else:
        current_tasks.append({"text": "Brak zadań płatniczych", "id": "fallback_pool2", "completed": False})

    random.shuffle(current_tasks)


# Funkcja pomocnicza do dzielenia tekstu na linie i obliczania wysokości bloku
def get_wrapped_lines_and_block_height(text_string, font_obj, max_width):
    words = text_string.split(' ')
    lines_text_only = []
    current_line_words_calc = []

    if not text_string.strip():  # Jeśli tekst jest pusty lub same białe znaki
        return [], 0

    for word in words:
        word_width = font_obj.size(word)[0]
        temp_line_words = current_line_words_calc + [word]
        temp_line = " ".join(temp_line_words)

        if font_obj.size(temp_line)[0] <= max_width:
            current_line_words_calc.append(word)
        else:
            if current_line_words_calc:  # Jeśli są słowa w obecnej linii
                lines_text_only.append(" ".join(current_line_words_calc))
            current_line_words_calc = [word]
            if font_obj.size(word)[0] > max_width:
                lines_text_only.append(word)
                current_line_words_calc = []

    if current_line_words_calc:  # Dodaj ostatnią linię
        lines_text_only.append(" ".join(current_line_words_calc))

    if not lines_text_only and text_string:
        lines_text_only.append(text_string)

    block_height = 0
    if lines_text_only:
        for i_line in range(len(lines_text_only)):
            block_height += font_obj.get_height()
            if i_line < len(lines_text_only) - 1:
                block_height += LINE_SPACING_INSIDE_TASK
    return lines_text_only, block_height


def draw_task_board():
    board_width = 450
    padding = 15
    line_spacing_after_title = 10
    line_spacing_between_tasks = 10
    icon_text_spacing = 10

    required_height = padding
    title_surf_calc = render_text_with_outline(task_font, "Lista Zadań:", WHITE, BLACK, 1)
    required_height += title_surf_calc.get_height()
    required_height += line_spacing_after_title

    max_text_width_for_task = board_width - (2 * padding) - TASK_ICON_SIZE[0] - icon_text_spacing

    calculated_task_data = []

    for task in current_tasks:
        lines_strings, text_block_h = get_wrapped_lines_and_block_height(
            task["text"], task_font, max_text_width_for_task
        )
        calculated_task_data.append((lines_strings, text_block_h))
        visual_block_height = max(TASK_ICON_SIZE[1], text_block_h)
        required_height += visual_block_height + line_spacing_between_tasks

    if current_tasks:
        required_height -= line_spacing_between_tasks
    required_height += padding

    board_height = required_height

    task_board_surface = pygame.Surface((board_width, board_height), pygame.SRCALPHA)
    task_board_surface.fill(TASK_BOARD_BG_COLOR)

    task_board_surface.blit(title_surf_calc, (padding, padding))
    current_y = padding + title_surf_calc.get_height() + line_spacing_after_title

    for i, task in enumerate(current_tasks):
        icon = check_mark_img if task["completed"] else cross_mark_img
        lines_strings, text_block_h = calculated_task_data[i]

        visual_block_height_for_entry = max(TASK_ICON_SIZE[1], text_block_h)

        icon_y_pos = current_y + (visual_block_height_for_entry - TASK_ICON_SIZE[1]) // 2
        task_board_surface.blit(icon, (padding, icon_y_pos))

        line_render_y = current_y + (visual_block_height_for_entry - text_block_h) // 2

        for line_str in lines_strings:
            line_surface = render_text_with_outline(task_font, line_str, WHITE, BLACK, 1)
            task_board_surface.blit(line_surface, (padding + TASK_ICON_SIZE[0] + icon_text_spacing, line_render_y))
            line_render_y += line_surface.get_height() + LINE_SPACING_INSIDE_TASK

        current_y += visual_block_height_for_entry + line_spacing_between_tasks

    screen.blit(task_board_surface, (10, 10))


# --- Koniec logiki zadań ---


# Funkcje pomocnicze
def render_text_with_outline(font_obj, text, text_color, outline_color,
                             outline_thickness=1):
    text_width, text_height = font_obj.size(text)
    if not text.strip():
        return pygame.Surface((1, 1), pygame.SRCALPHA)

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


def render_text_wrapped(text_string, font_obj, text_color,
                        max_width):
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
    line_spacing_val = 2
    for i, line_text in enumerate(lines_text):
        if line_text.strip():
            text_surf = font_obj.render(line_text, True, text_color)
            surfaces.append(text_surf)
            total_height += text_surf.get_height()
            if i < len(lines_text) - 1:
                total_height += line_spacing_val
    return surfaces, total_height


# Konfiguracja obiektów
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
background = pygame.image.load("background/map.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))
background1 = pygame.image.load("background/payments.png").convert()
background1 = pygame.transform.scale(background1, (WIDTH, HEIGHT))
background2 = pygame.image.load("background/PE_enrollment.png").convert()
background2 = pygame.transform.scale(background2, (WIDTH, HEIGHT))
background3 = pygame.image.load("background/grades.png").convert()
background3 = pygame.transform.scale(background3, (WIDTH, HEIGHT))

# Maski kolizji
road_mask = pygame.image.load("background/map_mask.png").convert_alpha()
road_mask = pygame.transform.scale(road_mask, (WIDTH, HEIGHT))
payments_mask = pygame.image.load("background/payments_mask.png").convert_alpha()
payments_mask = pygame.transform.scale(payments_mask, (WIDTH, HEIGHT))
pe_enrollment_mask = pygame.image.load("background/PE_enrollment_mask.png").convert_alpha()
pe_enrollment_mask = pygame.transform.scale(pe_enrollment_mask, (WIDTH, HEIGHT))
grades_mask = pygame.image.load("background/grades_mask.png").convert_alpha()
grades_mask = pygame.transform.scale(grades_mask, (WIDTH, HEIGHT))

# Postać
PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100
prawo_img = pygame.image.load("characters and vehicles/character_right.png").convert_alpha()
prawo_img = pygame.transform.scale(prawo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
prawo_idzie_img = pygame.image.load("characters and vehicles/character_right_move.png").convert_alpha()
prawo_idzie_img = pygame.transform.scale(prawo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_img = pygame.image.load("characters and vehicles/character_left.png").convert_alpha()
lewo_img = pygame.transform.scale(lewo_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
lewo_idzie_img = pygame.image.load("characters and vehicles/character_left_move.png").convert_alpha()
lewo_idzie_img = pygame.transform.scale(lewo_idzie_img, (PLAYER_WIDTH, PLAYER_HEIGHT))

# === NOWA LOGIKA GARAŻU I POJAZDÓW ===
CAR_SIZE = (70, 70)


def create_tinted_surface(surface, tint_color):
    """Tworzy zabarwioną wersję powierzchni, zachowując przezroczystość."""
    tinted_surf = surface.copy()
    tinted_surf.fill(tint_color, special_flags=pygame.BLEND_RGBA_MULT)
    return tinted_surf


# Ładowanie bazowych obrazków
base_car_left = pygame.transform.scale(pygame.image.load("characters and vehicles/car_left.png").convert_alpha(), CAR_SIZE)
base_car_right = pygame.transform.scale(pygame.image.load("characters and vehicles/car_right.png").convert_alpha(), CAR_SIZE)
base_car_up = pygame.transform.scale(pygame.image.load("characters and vehicles/car_up.png").convert_alpha(), CAR_SIZE)
base_car_down = pygame.transform.scale(pygame.image.load("characters and vehicles/car_down.png").convert_alpha(), CAR_SIZE)

# Baza danych pojazdów
vehicle_database = {
    'default': {
        'name': 'Czerwony Sportowy',
        'price': 0,
        'images': {
            "left": base_car_left,
            "right": base_car_right,
            "up": base_car_up,
            "down": base_car_down
        }
    },
    'blue_car': {
        'name': 'Niebieski Miejski',
        'price': 150,
        'images': {
            "left": create_tinted_surface(base_car_left, (100, 100, 255)),
            "right": create_tinted_surface(base_car_right, (100, 100, 255)),
            "up": create_tinted_surface(base_car_up, (100, 100, 255)),
            "down": create_tinted_surface(base_car_down, (100, 100, 255))
        }
    },
    'green_van': {
        'name': 'Zielony Van',
        'price': 300,
        'images': {
            "left": create_tinted_surface(base_car_left, (50, 150, 50)),
            "right": create_tinted_surface(base_car_right, (50, 150, 50)),
            "up": create_tinted_surface(base_car_up, (50, 150, 50)),
            "down": create_tinted_surface(base_car_down, (50, 150, 50))
        }
    }
}

# Stan posiadania pojazdów gracza
owned_vehicles = ['default']
current_vehicle_id = 'default'

# Ikona garażu
GARAGE_ICON_SIZE = (60, 60)
garage_icon_surf = pygame.Surface(GARAGE_ICON_SIZE, pygame.SRCALPHA)
garage_icon_surf.fill((100, 100, 100, 180))
pygame.draw.rect(garage_icon_surf, WHITE, (5, 25, 50, 30))  # Baza garażu
pygame.draw.polygon(garage_icon_surf, WHITE, [(2, 25), (30, 5), (58, 25)])  # Dach
garage_icon_rect = None  # Zostanie zainicjowany później


# ==========================================


# === NOWA KLASA DLA ZDALNYCH GRACZY ===
class RemotePlayer:
    def __init__(self, state_dict):
        self.id = state_dict.get("id")
        self.animation_frame = 0
        self.animation_counter = 0
        self.update_state(state_dict)

    def update_state(self, state_dict):
        self.x = state_dict.get("x", 0)
        self.y = state_dict.get("y", 0)
        self.facing = state_dict.get("facing", "prawo")
        self.is_moving = state_dict.get("is_moving", False)
        self.image_type = state_dict.get("image_type", "car")
        self.car_direction = state_dict.get("car_direction", "right")
        self.current_background_id = state_dict.get("current_background_id", 0)
        self.color = state_dict.get("color", (255, 0, 255))  # Różowy jako fallback
        # === ZMIANA: Odczytywanie ID pojazdu zdalnego gracza ===
        self.vehicle_id = state_dict.get("vehicle_id", "default")


        # Logika animacji dla zdalnego gracza
        if self.image_type == "character" and self.is_moving:
            self.animation_counter += 1
            if self.animation_counter >= 10:
                self.animation_counter = 0
                self.animation_frame = 1 - self.animation_frame
        else:
            self.animation_frame = 0
            self.animation_counter = 0

    def draw(self, surface):
        img_to_draw = None
        if self.image_type == "car":
            # === ZMIANA: Używanie vehicle_id do wyboru odpowiedniego obrazka ===
            # Używamy .get() dla bezpieczeństwa, na wypadek gdyby ID nie istniało - wtedy wróci do default.
            vehicle_images = vehicle_database.get(self.vehicle_id, vehicle_database['default'])['images']
            img_to_draw = vehicle_images.get(self.car_direction)
            if img_to_draw:
                surface.blit(img_to_draw, (self.x, self.y))

        elif self.image_type == "character":
            if self.facing == "prawo":
                img_to_draw = prawo_idzie_img if self.animation_frame == 1 else prawo_img
            else:  # lewo
                img_to_draw = lewo_idzie_img if self.animation_frame == 1 else lewo_img

            if img_to_draw:
                surface.blit(img_to_draw, (self.x, self.y))

        # Rysuj etykietę z ID nad graczem
        label = render_text_with_outline(font, f"Gracz {self.id}", WHITE, BLACK)
        label_rect = label.get_rect(center=(
            self.x + PLAYER_WIDTH // 2 if self.image_type == 'character' else self.x + CAR_SIZE[0] // 2, self.y - 15))
        surface.blit(label, label_rect)


# ==========================================


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
subjects = [
    "podstawy /programowania", "analiza /matematyczna", "programowanie /obiektowe",
    "angielski", "Fizyka dla informatyków /i analityków danych"
]
grades = {
    subject: [random.randint(2, 5) for _ in range(random.randint(3, 5))]
    for subject in subjects
}

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
            squares_to_draw = PE_SQUARES_2
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


def handle_grades_display():
    grades_bg_rect = grades_bg.get_rect(topleft=(grades_bg_x, grades_bg_y))
    screen.blit(grades_bg, grades_bg_rect)
    pygame.draw.rect(screen, BLACK, grades_bg_rect, 2)
    y_offset = grades_bg_rect.y + 25
    x_start = grades_bg_rect.x + 25
    max_subject_width_grades = grades_bg_width * 0.48
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
                                                                             max_subject_width_grades)
            temp_y = current_render_y
            for line_surf in rendered_lines_surfaces:
                screen.blit(line_surf, (x_start, temp_y))
                temp_y += line_surf.get_height() + line_spacing_for_wrapped_subject
            current_render_y = temp_y
            if rendered_lines_surfaces:
                current_render_y -= line_spacing_for_wrapped_subject
            total_rendered_subject_height = current_render_y - original_y_for_this_subject_entry
        grade_x = x_start + max_subject_width_grades + spacing_after_subject
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
active_coins_list = []
MAX_ACTIVE_COINS = 10
COIN_SPAWN_INTERVAL = 5000
last_coin_spawn_time = pygame.time.get_ticks()

coin_spawn_cooldowns = {}
COIN_SPOT_COOLDOWN_DURATION = 15000
MAX_SPAWN_ATTEMPTS = 50
last_cooldown_cleanup_time = pygame.time.get_ticks()


def get_random_coin_spawn_position():
    rand_x = random.randint(0, WIDTH - COIN_SIZE[0])
    rand_y = random.randint(0, HEIGHT - COIN_SIZE[1])
    return (rand_x, rand_y)


def spawn_coin():
    global active_coins_list, coin_spawn_cooldowns
    current_time_ticks = pygame.time.get_ticks()
    if len(active_coins_list) < MAX_ACTIVE_COINS:
        for _ in range(MAX_SPAWN_ATTEMPTS):
            potential_pos = get_random_coin_spawn_position()
            if potential_pos in active_coins_list:
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
                active_coins_list.append(potential_pos)
                coin_spawn_cooldowns[potential_pos] = current_time_ticks + COIN_SPOT_COOLDOWN_DURATION
                return


# --- Koniec logiki monet ---

# --- Menu startowe/pauzy ---
try:
    gear_icon_original = pygame.image.load("graphics icons/gear.png").convert_alpha()
    GEAR_ICON_SIZE = (100, 100)
    gear_icon = pygame.transform.scale(gear_icon_original, GEAR_ICON_SIZE)
    gear_icon_rect = gear_icon.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))
except pygame.error as e:
    print(f"Ostrzeżenie: Nie udało się załadować gear.png: {e}. Ikona ustawień nie będzie dostępna.")
    gear_icon = None
    gear_icon_rect = None


def start_screen(is_pause_menu=False):
    title_font = pygame.font.Font('fonts/munro.ttf', 100)
    button_font = pygame.font.Font('fonts/munro.ttf', 50)
    title_text_content = "Ustawienia" if is_pause_menu else "Car Dziekanat"
    start_button_text_content = "Wznów" if is_pause_menu else "Start"
    button_width = 300
    button_height = 80
    start_button = pygame.Rect(WIDTH / 2 - button_width / 2, HEIGHT / 2 - button_height / 2 - 50, button_width,
                               button_height)
    exit_button = pygame.Rect(WIDTH / 2 - button_width / 2, HEIGHT / 2 + button_height / 2 + 10, button_width,
                              button_height)

    game_screen_capture = None
    if is_pause_menu:
        game_screen_capture = screen.copy()

    menu_running = True
    while menu_running:
        mouse_pos = pygame.mouse.get_pos()

        if is_pause_menu and game_screen_capture:
            screen.blit(game_screen_capture, (0, 0))
            overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 150))
            screen.blit(overlay_surface, (0, 0))
        elif not is_pause_menu:
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


# === NOWA FUNKCJA INTERFEJSU GARAŻU ===
def garage_screen():
    global coins, current_vehicle_id, owned_vehicles

    game_screen_capture = screen.copy()
    menu_running = True

    # Układ interfejsu
    bg_rect = pygame.Rect(WIDTH * 0.1, HEIGHT * 0.1, WIDTH * 0.8, HEIGHT * 0.8)
    title_font = pygame.font.Font('fonts/munro.ttf', 70)
    vehicle_font = pygame.font.Font('fonts/munro.ttf', 35)
    button_font = pygame.font.Font('fonts/munro.ttf', 30)

    button_rects = {}  # Słownik do przechowywania rectów przycisków

    while menu_running:
        mouse_pos = pygame.mouse.get_pos()

        screen.blit(game_screen_capture, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Tło menu
        pygame.draw.rect(screen, (40, 40, 60), bg_rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, bg_rect, width=3, border_radius=20)

        # Tytuł
        title_surf = render_text_with_outline(title_font, "Garaż", WHITE, BLACK, 2)
        screen.blit(title_surf, title_surf.get_rect(centerx=bg_rect.centerx, top=bg_rect.top + 20))

        # Informacja o monetach
        coins_text_surf = render_text_with_outline(garage_font, f"Twoje monety: {coins}", YELLOW, BLACK)
        screen.blit(coins_text_surf, coins_text_surf.get_rect(centerx=bg_rect.centerx, top=bg_rect.top + 100))

        # Lista pojazdów
        current_y = bg_rect.top + 180
        item_height = 120

        button_rects.clear()

        for vehicle_id, vehicle_data in vehicle_database.items():
            item_rect = pygame.Rect(bg_rect.left + 20, current_y, bg_rect.width - 40, item_height - 10)
            pygame.draw.rect(screen, (60, 60, 80) if item_rect.collidepoint(mouse_pos) else (50, 50, 70), item_rect,
                             border_radius=10)

            # Obrazek pojazdu
            img = vehicle_data['images']['right']
            img_rect = img.get_rect(centery=item_rect.centery, left=item_rect.left + 20)
            screen.blit(img, img_rect)

            # Nazwa pojazdu
            name_surf = vehicle_font.render(vehicle_data['name'], True, WHITE)
            screen.blit(name_surf, (img_rect.right + 20, item_rect.top + 20))

            # Przyciski i status
            button_width, button_height = 200, 50
            button_x = item_rect.right - button_width - 20
            button_y = item_rect.centery - button_height // 2

            btn_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button_rects[vehicle_id] = btn_rect  # Zapisz rect przycisku

            if vehicle_id in owned_vehicles:
                if vehicle_id == current_vehicle_id:
                    status_text = "Wybrany"
                    btn_color = (80, 80, 80)  # Szary
                    text_color = GREY
                else:
                    status_text = "Wybierz"
                    btn_color = BLUE if btn_rect.collidepoint(mouse_pos) else (0, 0, 180)
                    text_color = WHITE
            else:
                price = vehicle_data['price']
                status_text = f"Kup ({price})"
                if coins >= price:
                    btn_color = GREEN if btn_rect.collidepoint(mouse_pos) else (0, 150, 0)
                    text_color = WHITE
                else:
                    btn_color = (80, 80, 80)  # Szary
                    text_color = GREY

            pygame.draw.rect(screen, btn_color, btn_rect, border_radius=10)
            btn_text_surf = button_font.render(status_text, True, text_color)
            screen.blit(btn_text_surf, btn_text_surf.get_rect(center=btn_rect.center))

            # Cena dla nieposiadanych pojazdów
            if vehicle_id not in owned_vehicles:
                price_surf = vehicle_font.render(f"Cena: {vehicle_data['price']}", True, YELLOW)
                screen.blit(price_surf, (img_rect.right + 20, item_rect.top + 60))

            current_y += item_height

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                menu_running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Sprawdź kliknięcia przycisków
                for vehicle_id, rect in button_rects.items():
                    if rect.collidepoint(event.pos):
                        vehicle_data = vehicle_database[vehicle_id]
                        if vehicle_id in owned_vehicles:
                            if vehicle_id != current_vehicle_id:
                                current_vehicle_id = vehicle_id
                                print(f"[GARAŻ] Wybrano pojazd: {vehicle_data['name']}")
                        else:  # Logika zakupu
                            price = vehicle_data['price']
                            if coins >= price:
                                coins -= price
                                owned_vehicles.append(vehicle_id)
                                print(f"[GARAŻ] Zakupiono pojazd: {vehicle_data['name']} za {price} monet.")
                            else:
                                print(f"[GARAŻ] Za mało monet, by kupić {vehicle_data['name']}.")
                        break  # Przerwij pętlę po znalezieniu klikniętego przycisku
                else:  # Jeśli nie kliknięto żadnego przycisku
                    if not bg_rect.collidepoint(event.pos):
                        menu_running = False

        pygame.display.flip()
        clock.tick(FPS)


# =======================================

# --- Koniec Menu ---

start_screen(is_pause_menu=False)
generate_tasks()

# === INICJALIZACJA SIECI ===
network = Network("127.0.0.1", 5555)
initial_state = network.connect()

if initial_state is None:
    print("Nie udało się połączyć z serwerem. Zamykanie programu.")
    pygame.quit()
    sys.exit()

my_id = network.player_id
car_x = initial_state.get('x', car_x)
car_y = initial_state.get('y', car_y)
remote_players = {}
# ===========================

running = True
while running:
    current_time = pygame.time.get_ticks()
    active_message = None

    if pygame.time.get_ticks() - coin_animation_timer > COIN_ANIMATION_SPEED:
        current_coin_frame_index = (current_coin_frame_index + 1) % len(coin_frames)
        coin_animation_timer = pygame.time.get_ticks()
    active_coin_image = coin_frames[current_coin_frame_index]

    # --- LOGIKA SIECIOWA: Zbieranie i wysyłanie danych ---
    # Ustal obecny stan do wysłania
    image_type_to_send = "character" if inside_building else "car"
    current_x = character_x if inside_building else car_x
    current_y = character_y if inside_building else car_y

    # Ustal ID aktualnego tła
    bg_id = 0
    if current_background == background1:
        bg_id = 1
    elif current_background == background2:
        bg_id = 2
    elif current_background == background3:
        bg_id = 3

    # === ZMIANA: Dodanie ID pojazdu do wysyłanego stanu ===
    local_player_state_to_send = {
        "id": my_id,
        "x": current_x,
        "y": current_y,
        "facing": facing,
        "is_moving": is_moving,
        "image_type": image_type_to_send,
        "car_direction": car_direction,
        "current_background_id": bg_id,
        "vehicle_id": current_vehicle_id  # <-- DODANA LINIA
    }

    # Wyślij stan i odbierz stan wszystkich graczy
    all_players_data = network.send(local_player_state_to_send)

    # Przetwórz otrzymane dane o graczach
    if all_players_data:
        current_player_ids_on_server = set()
        for p_data in all_players_data:
            p_id = p_data["id"]
            current_player_ids_on_server.add(p_id)

            if p_id == my_id:
                continue

            if p_id not in remote_players:
                remote_players[p_id] = RemotePlayer(p_data)
                print(f"[INFO] Gracz {p_id} dołączył do gry.")
            else:
                remote_players[p_id].update_state(p_data)

        # Usuń graczy, którzy się rozłączyli
        disconnected_ids = set(remote_players.keys()) - current_player_ids_on_server
        for p_id_to_remove in disconnected_ids:
            print(f"[INFO] Gracz {p_id_to_remove} opuścił grę.")
            del remote_players[p_id_to_remove]
    else:  # Jeśli utracono połączenie
        print("[BŁĄD] Utracono połączenie z serwerem.")
        running = False
        continue  # Przejdź do następnej iteracji, aby zakończyć pętlę

    # --- KONIEC LOGIKI SIECIOWEJ ---

    screen.blit(current_background, (0, 0))

    # UI W PRAWMYM GÓRNYM ROGU (MONETY I GARAŻ)
    coins_text_surf = font.render(f"{coins}", True, BLACK)
    coins_text_rect = coins_text_surf.get_rect(topright=(WIDTH - 10, 10))
    screen.blit(coins_text_surf, coins_text_rect)
    coin_display_rect = active_coin_image.get_rect(topright=(
        coins_text_rect.left - 5, coins_text_rect.top + (coins_text_rect.height - active_coin_image.get_height()) // 2))
    screen.blit(active_coin_image, coin_display_rect)

    # Rysowanie ikony garażu
    garage_icon_rect = garage_icon_surf.get_rect(topright=(coin_display_rect.left - 15, coin_display_rect.top))
    screen.blit(garage_icon_surf, garage_icon_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if gear_icon and gear_icon_rect and gear_icon_rect.collidepoint(event.pos):
                    start_screen(is_pause_menu=True)
                # NOWY WARUNEK - KLIKNIĘCIE IKONY GARAŻU
                if garage_icon_rect and garage_icon_rect.collidepoint(event.pos) and not inside_building:
                    garage_screen()

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

                    interaction_made_this_press = False
                    for sq_info in target_squares:
                        if interaction_made_this_press: break

                        sq_rect = pygame.Rect(sq_info["rect"])
                        if player_interaction_rect.colliderect(sq_rect):
                            action_id = sq_info["message"]
                            action_message_time = current_time
                            interaction_made_this_press = True

                            current_action_feedback = f"{action_id}: Akcja!"

                            if action_id == "Tablica ocen":
                                show_grades = not show_grades
                                task_found_for_grades = False
                                for task_obj in current_tasks:
                                    if task_obj["id"] == "Tablica ocen":
                                        task_found_for_grades = True
                                        if not task_obj["completed"] and show_grades:
                                            task_obj["completed"] = True
                                            coins += 50
                                            current_action_feedback = f"Zadanie '{task_obj['text']}' wykonane! +50 monet"
                                        elif task_obj["completed"]:
                                            current_action_feedback = f"Zadanie '{task_obj['text']}' już wykonane. Oceny " + (
                                                "pokazane." if show_grades else "ukryte.")
                                        else:
                                            current_action_feedback = "Oceny ukryte."
                                        break
                                if not task_found_for_grades:
                                    current_action_feedback = "To nie jest Twoje zadanie. Oceny " + (
                                        "pokazane." if show_grades else "ukryte.")
                                action_message = current_action_feedback

                            else:
                                task_found_regular = False
                                for task_obj in current_tasks:
                                    if task_obj["id"] == action_id:
                                        task_found_regular = True
                                        if not task_obj["completed"]:
                                            task_obj["completed"] = True
                                            coins += 50
                                            current_action_feedback = f"Zadanie '{task_obj['text']}' wykonane! +50 monet"
                                        else:
                                            current_action_feedback = f"Zadanie '{task_obj['text']}' już wykonane."
                                        break
                                if not task_found_regular:
                                    current_action_feedback = "To nie jest Twoje zadanie."
                                action_message = current_action_feedback
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
        moved_this_frame = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_velocity_x_char = max(-max_speed_char, new_velocity_x_char - acceleration_char)
            facing = "lewo";
            moved_this_frame = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_velocity_x_char = min(max_speed_char, new_velocity_x_char + acceleration_char)
            facing = "prawo";
            moved_this_frame = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_velocity_y_char = max(-max_speed_char, new_velocity_y_char - acceleration_char)
            moved_this_frame = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_velocity_y_char = min(max_speed_char, new_velocity_y_char + acceleration_char)
            moved_this_frame = True

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
        is_moving = moved_this_frame or abs(velocity_x_char) > 0.1 or abs(velocity_y_char) > 0.1

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
                (int(character_x + PLAYER_WIDTH * 0.5), int(character_y + PLAYER_HEIGHT * 0.95))]
            collision_detected = False
            for p_x, p_y in player_points_to_check:
                if not (0 <= p_x < WIDTH and 0 <= p_y < HEIGHT) or \
                        mask_to_check.get_at((p_x, p_y))[0:3] != (255, 255, 255):
                    collision_detected = True;
                    break
            if collision_detected:
                character_x, character_y = prev_char_x, prev_char_y
                velocity_x_char, velocity_y_char = 0, 0

        character_x = max(0, min(character_x, WIDTH - PLAYER_WIDTH))
        character_y = max(0, min(character_y, HEIGHT - PLAYER_HEIGHT))

        # RYSOWANIE LOKALNEGO GRACZA
        update_animation()
        screen.blit(get_player_image(), (character_x, character_y))

        if current_background == background3 and show_grades:
            handle_grades_display()

        player_rect_center_x = character_x + PLAYER_WIDTH // 2
        player_rect_center_y = character_y + PLAYER_HEIGHT // 2
        player_interaction_rect_for_msg = pygame.Rect(player_rect_center_x - 10, player_rect_center_y - 10, 20, 20)
        target_squares_for_msg = []
        if current_background == background1:
            target_squares_for_msg = PAYMENTS_SQUARES
        elif current_background == background2:
            target_squares_for_msg = PE_SQUARES_2
        elif current_background == background3:
            target_squares_for_msg = GRADES_SQUARES

        if not (action_message and current_time - action_message_time < 2000):
            for sq_info in target_squares_for_msg:
                if player_interaction_rect_for_msg.colliderect(pygame.Rect(sq_info["rect"])):
                    active_message = sq_info["message"]
                    break
    else:
        new_car_direction = car_direction
        new_velocity_x_car, new_velocity_y_car = velocity_x_car, velocity_y_car
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: new_velocity_x_car = max(-max_speed_car,
                                                                             new_velocity_x_car - acceleration_car); new_car_direction = "left"
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: new_velocity_x_car = min(max_speed_car,
                                                                              new_velocity_x_car + acceleration_car); new_car_direction = "right"
        if keys[pygame.K_UP] or keys[pygame.K_w]: new_velocity_y_car = max(-max_speed_car,
                                                                           new_velocity_y_car - acceleration_car); new_car_direction = "up"
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: new_velocity_y_car = min(max_speed_car,
                                                                             new_velocity_y_car + acceleration_car); new_car_direction = "down"

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
            building_entry_rect = pygame.Rect(bx - 10, by - 10, 50 + 20, 50 + 20)
            if car_rect_check.colliderect(building_entry_rect):
                near_building = (bx, by);
                break

        # RYSOWANIE LOKALNEGO GRACZA - ZMODYFIKOWANE
        car_image_to_blit = vehicle_database[current_vehicle_id]['images'][car_direction]
        screen.blit(car_image_to_blit, (car_x, car_y))

        car_collision_rect = pygame.Rect(car_x, car_y, CAR_SIZE[0], CAR_SIZE[1])
        for coin_pos in active_coins_list[:]:
            coin_rect = pygame.Rect(coin_pos[0], coin_pos[1], COIN_SIZE[0], COIN_SIZE[1])
            if car_collision_rect.colliderect(coin_rect):
                coins += 1
                active_coins_list.remove(coin_pos)

        if near_building:
            text_surf = render_text_with_outline(font, "Wciśnij E", BLACK, YELLOW)
            text_rect_clamped = get_clamped_text_rect(text_surf, (car_x, car_y))
            screen.blit(text_surf, text_rect_clamped)

        if current_time - last_coin_spawn_time > COIN_SPAWN_INTERVAL:
            spawn_coin()
            last_coin_spawn_time = current_time

        if current_time - last_cooldown_cleanup_time > 60000:
            expired_keys = [k for k, v in coin_spawn_cooldowns.items() if current_time > v]
            for k in expired_keys: del coin_spawn_cooldowns[k]
            last_cooldown_cleanup_time = current_time

    if not inside_building:
        for c_pos in active_coins_list:
            screen.blit(active_coin_image, c_pos)

    # === RYSOWANIE INNYCH GRACZY ===
    for player_obj in remote_players.values():
        if player_obj.current_background_id == bg_id:  # Rysuj tylko graczy w tej samej "scenie"
            player_obj.draw(screen)
    # ===============================

    draw_interaction_indicators()

    display_message_final = None
    if action_message and current_time - action_message_time < 2000:
        display_message_final = action_message
    elif active_message and inside_building:
        display_message_final = active_message

    if display_message_final:
        message_surf = render_text_with_outline(font, display_message_final, BLACK, YELLOW)
        if inside_building:
            message_rect = message_surf.get_rect(center=(character_x + PLAYER_WIDTH // 2, character_y - 20))
            if message_rect.left < 0: message_rect.left = 0
            if message_rect.right > WIDTH: message_rect.right = WIDTH
            if message_rect.top < 0: message_rect.top = 0
            if message_rect.bottom > HEIGHT: message_rect.bottom = HEIGHT
        else:
            message_rect = message_surf.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        screen.blit(message_surf, message_rect)

    if gear_icon and gear_icon_rect:
        screen.blit(gear_icon, gear_icon_rect)

    draw_task_board()

    pygame.display.flip()
    clock.tick(FPS)

# --- Zamykanie połączenia ---
print("[ROZŁĄCZANIE] Zamykanie połączenia z serwerem...")
network.close()
# --------------------------
pygame.quit()
sys.exit()