import socket
import pickle
import threading
import random

# Konfiguracja serwera
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5555
BUFFER_SIZE = 4096

# Przechowywanie danych graczy
players_data = {}
player_id_counter = 0
lock = threading.Lock()

def handle_client(client_socket, client_address):
    global player_id_counter
    print(f"[NOWE POŁĄCZENIE] Połączono z {client_address}")

    with lock:
        current_player_id = player_id_counter
        player_id_counter += 1
        # === ZMIANA: Zaktualizowany stan początkowy, aby pasował do klienta script.py ===
        initial_player_state = {
            "id": current_player_id,
            "x": 1000,  # Pozycja startowa X (samochód)
            "y": 530,   # Pozycja startowa Y (samochód)
            "color": (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
            "message": "Połączono",
            "image_type": "car",  # Gracz zaczyna w samochodzie
            "car_direction": "right",
            "facing": "prawo", # Domyślne skierowanie postaci
            "is_moving": False,
            "current_background_id": 0 # 0 dla mapy głównej
        }
        players_data[client_address] = initial_player_state

    try:
        # Wyślij pakiet powitalny z ID i stanem początkowym
        client_socket.send(pickle.dumps({"id": current_player_id, "initial_state": players_data[client_address]}))
    except socket.error as e:
        print(f"[BŁĄD WYSYŁANIA ID] {e}")
        with lock:
            if client_address in players_data:
                del players_data[client_address]
        client_socket.close()
        return

    connected = True
    while connected:
        try:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                print(f"[ROZŁĄCZONO] {client_address} rozłączył się (brak danych).")
                break

            received_player_state = pickle.loads(data)

            with lock:
                if client_address in players_data:
                    players_data[client_address].update(received_player_state)
                else:
                    print(f"[OSTRZEŻENIE] Otrzymano dane od nieznanego klienta {client_address}")
                    continue

            with lock:
                all_players_list = list(players_data.values())

            client_socket.sendall(pickle.dumps(all_players_list))

        except socket.error as e:
            print(f"[BŁĄD SOCKETU] {client_address}: {e}")
            break
        except pickle.PickleError as e:
            print(f"[BŁĄD DESERIALIZACJI] {client_address}: {e}")
            continue
        except EOFError:
             print(f"[ROZŁĄCZONO] {client_address} zamknął połączenie (EOF).")
             break
        except Exception as e:
            print(f"[NIEOCZEKIWANY BŁĄD] {client_address}: {e}")
            break

    print(f"[ROZŁĄCZONO] {client_address} zakończył połączenie.")
    with lock:
        if client_address in players_data:
            del players_data[client_address]
    client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((SERVER_HOST, SERVER_PORT))
    except socket.error as e:
        print(f"[BŁĄD BINDOWANIA] Nie udało się zbindować adresu {SERVER_HOST}:{SERVER_PORT} - {e}")
        return

    server_socket.listen()
    print(f"[NASŁUCHIWANIE] Serwer nasłuchuje na {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            thread.daemon = True
            thread.start()
            print(f"[AKTYWNE POŁĄCZENIA] {threading.active_count() - 1}")
    except KeyboardInterrupt:
        print("\n[ZAMYKANIE] Serwer jest zamykany...")
    finally:
        server_socket.close()
        print("[ZAMKNIĘTY] Serwer został zamknięty.")

if __name__ == "__main__":
    main()