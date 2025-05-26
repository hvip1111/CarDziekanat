import pygame
import socket
import pickle
import random # For server-side player color, if needed by client
import sys

# --- Pygame/Game Constants (from script.py) ---
FPS = 60
WIDTH, HEIGHT = 800, 600

# Kolory
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
BLUE = (100, 100, 255)

PLAYER_WIDTH, PLAYER_HEIGHT = 100, 100 # For character
CAR_WIDTH, CAR_HEIGHT = 60, 60

# --- Network Class (from upload/client.py) ---
class Network:
    def __init__(self, server_host, server_port):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_host, server_port)
        self.player_id = None
        self.initial_player_state = None
        self.connect()

    def connect(self):
        try:
            self.client_socket.connect(self.server_address)
            initial_data_payload = self.client_socket.recv(4096)
            if not initial_data_payload:
                print("[BŁĄD POŁĄCZENIA] Nie otrzymano danych początkowych od serwera.")
                pygame.quit()
                sys.exit()
            initial_data = pickle.loads(initial_data_payload)
            self.player_id = initial_data.get("id")
            self.initial_player_state = initial_data.get("initial_state")
            print(f"[POŁĄCZONO] Pomyślnie połączono z serwerem. Twoje ID: {self.player_id}")
            # print(f"[STAN POCZĄTKOWY] {self.initial_player_state}")
            return self.initial_player_state
        except socket.error as e:
            print(f"[BŁĄD POŁĄCZENIA] Nie udało się połączyć z serwerem {self.server_address}: {e}")
            pygame.quit()
            sys.exit()
        except pickle.PickleError as e:
            print(f"[BŁĄD DESERIALIZACJI ID] {e}")
            pygame.quit()
            sys.exit()
        except EOFError:
            print("[BŁĄD POŁĄCZENIA] Serwer zamknął połączenie przed wysłaniem danych początkowych.")
            pygame.quit()
            sys.exit()

    def send(self, data):
        try:
            self.client_socket.send(pickle.dumps(data))
            response_payload = self.client_socket.recv(4096)
            if not response_payload:
                print("[BŁĄD SOCKETU] Nie otrzymano odpowiedzi od serwera.")
                return None
            return pickle.loads(response_payload)
        except socket.error as e:
            # print(f"[BŁĄD SOCKETU] Błąd podczas wysyłania/odbierania danych: {e}")
            return None
        except pickle.PickleError as e:
            print(f"[BŁĄD DESERIALIZACJI] Błąd podczas deserializacji odpowiedzi serwera: {e}")
            return None

    def close(self):
        self.client_socket.close()

# --- Asset Loading and Helper Functions (from script.py) ---
pygame.init() # Initialize Pygame early for font and image loading
screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Needed for convert_alpha()
pygame.display.set_caption("Gra Uczelniana Klient")

try:
    font = pygame.font.Font("munro.ttf", 18)
    subject_font = pygame.font.Font("munro.ttf", 17)
except pygame.error as e:
    print(f"Nie można załadować czcionki munro.ttf: {e}. Używam domyślnej czcionki.")
    font = pygame.font.Font(None, 24)
    subject_font = pygame.font.Font(None, 22)

def load_image(path, size=None, convert_alpha_flag=True):
    try:
        img = pygame.image.load(path)
        if size:
            img = pygame.transform.scale(img, size)
        return img.convert_alpha() if convert_alpha_flag else img.convert()
    except pygame.error as e:
        print(f"Nie można załadować obrazka: {path} - {e}")
        surface = pygame.Surface(size if size else (50,50))
        surface.fill(RED)
        if size:
            pygame.draw.line(surface, BLACK, (0,0), (size[0],size[1]), 1)
            pygame.draw.line(surface, BLACK, (0,size[1]), (size[0],0), 1)
        return surface

# Grafiki
background_images = {
    0: load_image("map.png", (WIDTH, HEIGHT), False), # Main map
    1: load_image("payments.png", (WIDTH, HEIGHT), False),
    2: load_image("PE_enrollment.png", (WIDTH, HEIGHT), False),
    3: load_image("grades.png", (WIDTH, HEIGHT), False)
}
# Maski kolizji (ładowane, ale używane tylko dla lokalnego gracza na razie)
# W grze sieciowej, walidacja kolizji powinna być na serwerze lub klient ufa serwerowi
road_mask = load_image("map_mask.png", (WIDTH, HEIGHT), False)
payments_mask = load_image("payments_mask.png", (WIDTH, HEIGHT), False)
pe_enrollment_mask = load_image("PE_enrollment_mask.png", (WIDTH, HEIGHT), False)
grades_mask = load_image("grades_mask.png", (WIDTH, HEIGHT), False)

collision_masks = {
    0: road_mask, 
    1: payments_mask, 
    2: pe_enrollment_mask, 
    3: grades_mask
}

# Postać
character_images = {
    "prawo": load_image("character_right.png", (PLAYER_WIDTH, PLAYER_HEIGHT)),
    "prawo_idzie": load_image("character_right_move.png", (PLAYER_WIDTH, PLAYER_HEIGHT)),
    "lewo": load_image("character_left.png", (PLAYER_WIDTH, PLAYER_HEIGHT)),
    "lewo_idzie": load_image("character_left_move.png", (PLAYER_WIDTH, PLAYER_HEIGHT))
}
# Pojazd
car_images = {
    "left": load_image("car_left.png", (CAR_WIDTH, CAR_HEIGHT)),
    "right": load_image("car_right.png", (CAR_WIDTH, CAR_HEIGHT)),
    "up": load_image("car_up.png", (CAR_WIDTH, CAR_HEIGHT)),
    "down": load_image("car_down.png", (CAR_WIDTH, CAR_HEIGHT))
}

def render_text_with_outline(f, text, text_color, outline_color, outline_thickness=1):
    text_width, text_height = f.size(text)
    surface_size = (text_width + 2 * outline_thickness, text_height + 2 * outline_thickness)
    text_surface = pygame.Surface(surface_size, pygame.SRCALPHA)
    for dx_ in range(-outline_thickness, outline_thickness + 1):
        for dy_ in range(-outline_thickness, outline_thickness + 1):
            if dx_ != 0 or dy_ != 0:
                text_outline = f.render(text, True, outline_color)
                text_surface.blit(text_outline, (dx_ + outline_thickness, dy_ + outline_thickness))
    text_main = f.render(text, True, text_color)
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

# --- Remote Player Class ---
class RemotePlayer:
    def __init__(self, player_id, state_dict):
        self.id = player_id
        self.x = state_dict.get("x", 50)
        self.y = state_dict.get("y", 50)
        self.facing = state_dict.get("facing", "prawo")
        self.is_moving = state_dict.get("is_moving", False)
        self.image_type = state_dict.get("image_type", "character") # "character" or "car"
        self.car_direction = state_dict.get("car_direction", "right")
        self.current_background_id = state_dict.get("current_background_id", 0)
        self.color = state_dict.get("color", (random.randint(50,200),random.randint(50,200),random.randint(50,200))) # Fallback color
        self.animation_frame = 0 # For remote player animation
        self.animation_counter = 0

    def update_state(self, state_dict):
        self.x = state_dict.get("x", self.x)
        self.y = state_dict.get("y", self.y)
        self.facing = state_dict.get("facing", self.facing)
        self.is_moving = state_dict.get("is_moving", self.is_moving)
        self.image_type = state_dict.get("image_type", self.image_type)
        self.car_direction = state_dict.get("car_direction", self.car_direction)
        self.current_background_id = state_dict.get("current_background_id", self.current_background_id)
        # self.color = state_dict.get("color", self.color) # Color might be fixed per player

        if self.image_type == "character" and self.is_moving:
            self.animation_counter += 1
            if self.animation_counter >= 10: # Match local animation speed
                self.animation_counter = 0
                self.animation_frame = 1 - self.animation_frame
        else:
            self.animation_frame = 0

    def draw(self, surface):
        img_to_draw = None
        pos_x, pos_y = self.x, self.y

        if self.image_type == "character":
            if self.facing == "prawo":
                img_to_draw = character_images["prawo_idzie"] if self.animation_frame else character_images["prawo"]
            else: # lewo
                img_to_draw = character_images["lewo_idzie"] if self.animation_frame else character_images["lewo"]
            pos_x -= PLAYER_WIDTH // 2 # Assuming x,y is center for character
            pos_y -= PLAYER_HEIGHT // 2
        elif self.image_type == "car":
            img_to_draw = car_images.get(self.car_direction)
            pos_x -= CAR_WIDTH // 2 # Assuming x,y is center for car
            pos_y -= CAR_HEIGHT // 2
        
        if img_to_draw:
            surface.blit(img_to_draw, (pos_x, pos_y))
        else: # Fallback if image type or direction is unknown
            pygame.draw.rect(surface, self.color, (pos_x - 15, pos_y - 15, 30, 30))

# --- Main Game Logic ---
def main():
    pygame.init() # Already called, but good practice in main
    clock = pygame.time.Clock()

    # Network Setup
    server_ip_input = input(f"Podaj adres IP serwera (domyślnie 127.0.0.1): ")
    current_server_host = server_ip_input if server_ip_input else "127.0.0.1"
    network = Network(current_server_host, 5555)

    if not network.initial_player_state: return
    local_player_id = network.player_id

    # Local Player State (adapted from script.py and initial server state)
    initial_state_from_server = network.initial_player_state
    local_character_x = initial_state_from_server.get("x", WIDTH // 2)
    local_character_y = initial_state_from_server.get("y", HEIGHT // 2)
    local_car_x = initial_state_from_server.get("x", WIDTH // 2)
    local_car_y = initial_state_from_server.get("y", HEIGHT - 100)
    
    local_facing = "prawo"
    local_is_moving = False
    local_animation_counter = 0
    local_current_frame = 0
    local_car_direction = "right"

    local_current_background_id = 0
    local_inside_building = False
    local_is_in_car = True

    entry_position = None
    near_building_coords = None
    active_message = None
    action_message = None
    action_message_time = 0
    show_grades = False
    
    speed_outside = 10
    speed_inside = 4

    buildings_interactive = [
        (100, 0, 1, "payments"), 
        (730, 225, 2, "pe_enrollments"), 
        (390, 380, 3, "grades")
    ]
    START_POSITIONS = {
        "payments": (400, 500),
        "pe_enrollments": (400, 500),
        "grades": (400, 500)
    }

    # Interaction squares - CORRECTED AND FULLY DEFINED
    PE_SQUARES = [
        {"rect": (90, 450, 50, 50), "message": "Siłownia"},
        {"rect": (100, 100, 50, 50), "message": "Ścianka wspinaczkowa"},
        {"rect": (400, 150, 50, 50), "message": "Siatka"},
        {"rect": (620, 250, 50, 50), "message": "Koszykówka"},
        {"rect": (600, 500, 50, 50), "message": "ping-pong"}
    ]
    PAYMENTS_SQUARES = [
        {"rect": (90, 380, 50, 50), "message": "ECTS"},
        {"rect": (270, 380, 50, 50), "message": "Akademik"},
        {"rect": (420, 310, 50, 50), "message": "Ubezpieczenie"},
        {"rect": (640, 380, 50, 50), "message": "Legitymacja"}
    ]
    GRADES_SQUARES = [
        {"rect": (700, 470, 50, 50), "message": "Tablica ocen"}
    ]

    remote_players = {} # {player_id: RemotePlayer_instance}

    running = True
    while running:
        current_pygame_time = pygame.time.get_ticks()
        active_message = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    if local_inside_building:
                        local_inside_building = False
                        local_is_in_car = True
                        local_current_background_id = 0
                        show_grades = False
                        if entry_position:
                            local_car_x, local_car_y = entry_position
                if event.key == pygame.K_e:
                    if local_inside_building:
                        player_rect_center_x = local_character_x
                        player_rect_center_y = local_character_y
                        player_rect = pygame.Rect(player_rect_center_x - PLAYER_WIDTH//2, player_rect_center_y - PLAYER_HEIGHT//2, PLAYER_WIDTH, PLAYER_HEIGHT)
                        
                        current_squares = []
                        if local_current_background_id == 1: current_squares = PAYMENTS_SQUARES
                        elif local_current_background_id == 2: current_squares = PE_SQUARES
                        elif local_current_background_id == 3: current_squares = GRADES_SQUARES

                        for sq_data in current_squares:
                            if player_rect.colliderect(pygame.Rect(sq_data["rect"])):
                                if local_current_background_id == 3:
                                    show_grades = not show_grades
                                else:
                                    action_message = "Akcja wykonana!"
                                    action_message_time = current_pygame_time
                                break
                    elif near_building_coords and local_is_in_car:
                        for b_x, b_y, target_bg_id, start_pos_key in buildings_interactive:
                            if (b_x, b_y) == near_building_coords:
                                local_inside_building = True
                                local_is_in_car = False
                                local_current_background_id = target_bg_id
                                entry_position = (local_car_x, local_car_y)
                                local_character_x, local_character_y = START_POSITIONS[start_pos_key]
                                break
        keys = pygame.key.get_pressed()
        local_is_moving = False

        prev_char_x, prev_char_y = local_character_x, local_character_y
        prev_car_x, prev_car_y = local_car_x, local_car_y

        if local_inside_building and not local_is_in_car:
            current_speed = speed_inside
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= current_speed; local_facing = "lewo"; local_is_moving = True
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += current_speed; local_facing = "prawo"; local_is_moving = True
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= current_speed; local_is_moving = True
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += current_speed; local_is_moving = True
            
            local_character_x += dx
            local_character_y += dy

            mask_to_check = collision_masks.get(local_current_background_id)
            try:
                if mask_to_check and mask_to_check.get_at((int(local_character_x), int(local_character_y))) != (255,255,255,255):
                    local_character_x, local_character_y = prev_char_x, prev_char_y
            except IndexError:
                 local_character_x, local_character_y = prev_char_x, prev_char_y

            local_character_x = max(PLAYER_WIDTH//2, min(local_character_x, WIDTH - PLAYER_WIDTH//2))
            local_character_y = max(PLAYER_HEIGHT//2, min(local_character_y, HEIGHT - PLAYER_HEIGHT//2))

            if local_is_moving:
                local_animation_counter += 1
                if local_animation_counter >= 10:
                    local_animation_counter = 0
                    local_current_frame = 1 - local_current_frame
            else:
                local_current_frame = 0
        
        elif not local_inside_building and local_is_in_car:
            current_speed = speed_outside
            dx, dy = 0, 0
            new_car_direction = local_car_direction
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx -= current_speed; new_car_direction = "left"
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += current_speed; new_car_direction = "right"
            if keys[pygame.K_UP] or keys[pygame.K_w]: dy -= current_speed; new_car_direction = "up"
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy += current_speed; new_car_direction = "down"
            local_car_direction = new_car_direction

            local_car_x += dx
            local_car_y += dy

            mask_to_check = collision_masks.get(0)
            try:
                if mask_to_check and mask_to_check.get_at((int(local_car_x), int(local_car_y))) != (255,255,255,255):
                    local_car_x, local_car_y = prev_car_x, prev_car_y
            except IndexError:
                local_car_x, local_car_y = prev_car_x, prev_car_y
            
            local_car_x = max(CAR_WIDTH//2, min(local_car_x, WIDTH - CAR_WIDTH//2))
            local_car_y = max(CAR_HEIGHT//2, min(local_car_y, HEIGHT - CAR_HEIGHT//2))

            near_building_coords = None
            for b_x, b_y, _, _ in buildings_interactive:
                if pygame.Rect(local_car_x - CAR_WIDTH, local_car_y - CAR_HEIGHT, CAR_WIDTH*2, CAR_HEIGHT*2).collidepoint(b_x + 25, b_y + 25):
                    near_building_coords = (b_x, b_y)
                    break

        current_x = local_character_x if local_inside_building else local_car_x
        current_y = local_character_y if local_inside_building else local_car_y
        image_type_to_send = "character" if local_inside_building else "car"

        local_player_state_to_send = {
            "id": local_player_id,
            "x": current_x,
            "y": current_y,
            "facing": local_facing,
            "is_moving": local_is_moving,
            "image_type": image_type_to_send,
            "car_direction": local_car_direction,
            "current_background_id": local_current_background_id
        }
        all_players_server_state = network.send(local_player_state_to_send)

        if all_players_server_state:
            current_player_ids_on_server = set()
            for p_data in all_players_server_state:
                p_id = p_data["id"]
                current_player_ids_on_server.add(p_id)

                if p_id == local_player_id:
                    continue
                
                if p_id not in remote_players:
                    remote_players[p_id] = RemotePlayer(p_id, p_data)
                    print(f"[NOWY GRACZ] Gracz {p_id} dołączył.")
                else:
                    remote_players[p_id].update_state(p_data)
            
            disconnected_ids = set(remote_players.keys()) - current_player_ids_on_server
            for p_id_to_remove in disconnected_ids:
                print(f"[GRACZ OPUŚCIŁ] Gracz {p_id_to_remove} rozłączył się.")
                del remote_players[p_id_to_remove]

        screen.blit(background_images[local_current_background_id], (0, 0))

        if local_inside_building and not local_is_in_car:
            img_key = local_facing + ("_idzie" if local_current_frame else "")
            char_img = character_images.get(img_key, character_images["prawo"])
            screen.blit(char_img, (local_character_x - PLAYER_WIDTH//2, local_character_y - PLAYER_HEIGHT//2))
        elif not local_inside_building and local_is_in_car:
            car_img = car_images.get(local_car_direction, car_images["right"])
            screen.blit(car_img, (local_car_x - CAR_WIDTH//2, local_car_y - CAR_HEIGHT//2))
            if near_building_coords:
                text_surface = render_text_with_outline(font, "Wciśnij E", BLACK, YELLOW)
                text_rect = get_clamped_text_rect(text_surface, (local_car_x, local_car_y - CAR_HEIGHT))
                screen.blit(text_surface, text_rect)

        for p_id, player_obj in remote_players.items():
            if player_obj.current_background_id == local_current_background_id:
                player_obj.draw(screen)
        
        if local_inside_building:
            player_rect_center_x = local_character_x
            player_rect_center_y = local_character_y
            player_rect = pygame.Rect(player_rect_center_x - PLAYER_WIDTH//2, player_rect_center_y - PLAYER_HEIGHT//2, PLAYER_WIDTH, PLAYER_HEIGHT)
            current_squares_for_msg = []
            if local_current_background_id == 1: current_squares_for_msg = PAYMENTS_SQUARES
            elif local_current_background_id == 2: current_squares_for_msg = PE_SQUARES
            elif local_current_background_id == 3: current_squares_for_msg = GRADES_SQUARES
            for sq_data in current_squares_for_msg:
                if player_rect.colliderect(pygame.Rect(sq_data["rect"])):
                    active_message = sq_data["message"]
                    break
            if active_message:
                msg_surface = render_text_with_outline(font, active_message, BLACK, YELLOW)
                msg_rect = get_clamped_text_rect(msg_surface, (local_character_x, local_character_y))
                screen.blit(msg_surface, msg_rect)
            if local_current_background_id == 3 and show_grades:
                # User should integrate their handle_grades_display() here
                grades_text_surface = pygame.Surface((420, 230))
                grades_text_surface.fill((160, 82, 45)) # grades_bg color
                pygame.draw.rect(grades_text_surface, BLACK, grades_text_surface.get_rect(), 2)
                # This is a placeholder for the actual grades drawing logic
                placeholder_text = font.render("Tablica Ocen (TODO: Pełna integracja)", True, BLACK)
                grades_text_surface.blit(placeholder_text, (10,10))
                screen.blit(grades_text_surface, (WIDTH//2 - 210, HEIGHT//2 - 115))

        if action_message and (current_pygame_time - action_message_time) < 2000:
            action_msg_surface = render_text_with_outline(font, action_message, BLACK, YELLOW)
            action_msg_rect = action_msg_surface.get_rect(center=(WIDTH // 2, 50))
            screen.blit(action_msg_surface, action_msg_rect)
        else:
            action_message = None

        pygame.display.flip()
        clock.tick(FPS)

    print("[ROZŁĄCZANIE] Zamykanie połączenia z serwerem...")
    network.close()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

