import time
import requests
import modi_plus
import json
import os

CONFIG_FILE = "client_config.json"

def get_server_url():
    """
    Gets the server URL. Tries to load from a config file first,
    otherwise prompts the user and saves it for next time.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                saved_url = config.get("server_url")
                if saved_url:
                    use_saved = input(f"Found saved server URL: {saved_url}. Use it? (Y/n): ").lower().strip()
                    if use_saved in ['', 'y', 'yes']:
                        return saved_url
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read config file. {e}")

    # Prompt for new URL if not found or not used
    server_url = input("Enter the full server address (e.g., http://192.168.1.10:8000 or https://your-ngrok-url.io): ")
    
    # Save the new URL
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"server_url": server_url}, f)
        print(f"Server URL saved to {CONFIG_FILE} for future use.")
    except IOError as e:
        print(f"Warning: Could not save config file. {e}")
        
    return server_url

def call_speak_endpoint(base_url, index):
    """Calls the server's speak endpoint."""
    try:
        url = f"{base_url}/speak/{index}"
        print(f"Calling endpoint: {url}")
        response = requests.post(url, timeout=None)
        response.raise_for_status()
        print("Server acknowledged speak request.")
    except requests.exceptions.RequestException as e:
        print(f"Error calling speak endpoint: {e}")

# -- State and Thresholds from main.py --
class State:
    FIND_EXTINGUISHER = -1
    START = 0
    ROTATE_TO_BREAK_TIE = 1
    PLACE_ON_FLOOR = 2
    PULL_PIN = 3
    AIM_NOZZLE = 4
    SQUEEZE_HANDLE = 5
    PREPARE_TO_FIRE = 6
    FIRE = 7
    EVACUATE = 8
    END = 9

# Thresholds for trigger sensitivity
ROTATION_VELOCITY_THRESHOLD = 10
SHAKE_ACCELERATION_THRESHOLD = 3
AIM_ANGLE_THRESHOLD = 45
PICK_UP_ACCELERATION_THRESHOLD = 40

def main():
    """Main simulation loop running on the MODI+ device."""
    server_base_url = get_server_url()
    current_state = State.FIND_EXTINGUISHER

    # -- MODI+ Initialization --
    try:
        print("Initializing MODI+ modules...")
        bundle = modi_plus.MODIPlus()
        imu = bundle.imus[0]
        button = bundle.buttons[0]
        speaker = bundle.speakers[0]
        print("Initialization complete. Starting simulation.")
        time.sleep(1)
    except Exception as e:
        print(f"Initialization error: {e}")
        print("Please ensure MODI+ IMU, Button, and Speaker are connected.")
        return

    # -- State Machine Loop --
    is_beeping = False
    beep_time = 0
    voice_played = False
    
    while current_state < State.END:
        try:
            # -- State Logic --
            if current_state == State.FIND_EXTINGUISHER:
                print("FIND_EXTINGUISHER mode. Press button to locate.", end='\r')
                if button.clicked:
                    print("\nButton clicked! Activating locator beep.")
                    is_beeping = True
                    beep_time = time.time()

                if is_beeping:
                    if time.time() - beep_time > 0.5:
                        speaker.set_tune(1500, 100)
                        time.sleep(0.1)
                        speaker.reset()
                        beep_time = time.time()
                    
                    acc_y = imu.acceleration_y
                    print(f"\rAcc Y: {acc_y:.2f} (threshold: {PICK_UP_ACCELERATION_THRESHOLD})", end="")
                    if abs(acc_y) > PICK_UP_ACCELERATION_THRESHOLD:
                        print("\nExtinguisher picked up!")
                        is_beeping = False
                        speaker.reset()
                        current_state = State.START
                        time.sleep(1)

            elif current_state == State.START:
                if not voice_played:
                    call_speak_endpoint(server_base_url, 0)
                    voice_played = True
                    print("Press button to proceed to next step.")
                if button.clicked:
                    print("Button clicked! Moving to next step.")
                    current_state = State.ROTATE_TO_BREAK_TIE
                    voice_played = False
                    time.sleep(1)

            elif current_state == State.ROTATE_TO_BREAK_TIE:
                print("Press button to rotate and break the tie.")
                if button.clicked:
                    print("Button clicked! Tie broken.")
                    call_speak_endpoint(server_base_url, 1)
                    current_state = State.PLACE_ON_FLOOR
                    time.sleep(2)

            elif current_state == State.PLACE_ON_FLOOR:
                print("Press button to place on floor.")
                if button.clicked:
                    print("Button clicked! Placed on floor.")
                    call_speak_endpoint(server_base_url, 2)
                    current_state = State.PULL_PIN
                    time.sleep(2)

            elif current_state == State.PULL_PIN:
                print("Press button to pull the pin.")
                if button.clicked:
                    print("Button clicked! Pin pulled.")
                    call_speak_endpoint(server_base_url, 3)
                    current_state = State.AIM_NOZZLE
                    time.sleep(2)

            elif current_state == State.AIM_NOZZLE:
                print("Press button to aim nozzle.")
                if button.clicked:
                    print("Button clicked! Nozzle aimed.")
                    call_speak_endpoint(server_base_url, 4)
                    current_state = State.SQUEEZE_HANDLE
                    time.sleep(3)

            elif current_state == State.SQUEEZE_HANDLE:
                call_speak_endpoint(server_base_url, 5)
                current_state = State.PREPARE_TO_FIRE
                time.sleep(3)

            elif current_state == State.PREPARE_TO_FIRE:
                call_speak_endpoint(server_base_url, 6)
                current_state = State.FIRE
                time.sleep(2)

            elif current_state == State.FIRE:
                call_speak_endpoint(server_base_url, 7)
                current_state = State.EVACUATE
                time.sleep(4)

            elif current_state == State.EVACUATE:
                call_speak_endpoint(server_base_url, 8)
                current_state = State.END

            time.sleep(0.1)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            # Optional: add reconnection logic here if needed
            break
            
    print("Simulation finished.")

if __name__ == "__main__":
    main()
