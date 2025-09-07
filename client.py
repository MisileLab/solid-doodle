import time
import requests
import modi_plus

# -- Server Communication --
def get_server_url():
    server_ip = input("Enter the IP address of the G-FIRE Assist server: ")
    return f"http://{server_ip}:8000"

def call_speak_endpoint(base_url, index):
    """Calls the server's speak endpoint."""
    try:
        url = f"{base_url}/speak/{index}"
        print(f"Calling endpoint: {url}")
        response = requests.post(url, timeout=5)
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
ROTATION_VELOCITY_THRESHOLD = 10000
SHAKE_ACCELERATION_THRESHOLD = 3
AIM_ANGLE_THRESHOLD = 45
PICK_UP_ACCELERATION_THRESHOLD = 1.5

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
                        speaker.set_tune(1500, 80)
                        time.sleep(0.1)
                        speaker.turn_off()
                        beep_time = time.time()
                    
                    acc_x, acc_y, acc_z = imu.acceleration_x, imu.acceleration_y, imu.acceleration_z
                    total_acc = (acc_x**2 + acc_y**2 + acc_z**2)**0.5
                    if total_acc > PICK_UP_ACCELERATION_THRESHOLD:
                        print("\nExtinguisher picked up!")
                        is_beeping = False
                        speaker.turn_off()
                        current_state = State.START
                        time.sleep(1)

            elif current_state == State.START:
                call_speak_endpoint(server_base_url, 0)
                current_state = State.ROTATE_TO_BREAK_TIE

            elif current_state == State.ROTATE_TO_BREAK_TIE:
                if abs(imu.angular_vel_z) > ROTATION_VELOCITY_THRESHOLD:
                    print("Rotation detected!")
                    call_speak_endpoint(server_base_url, 1)
                    current_state = State.PLACE_ON_FLOOR
                    time.sleep(2)

            elif current_state == State.PLACE_ON_FLOOR:
                if abs(imu.roll) > 70:
                    print("Placed on floor detected!")
                    call_speak_endpoint(server_base_url, 2)
                    current_state = State.PULL_PIN
                    time.sleep(2)

            elif current_state == State.PULL_PIN:
                acc_x, acc_y, acc_z = imu.acceleration_x, imu.acceleration_y, imu.acceleration_z
                total_acc = (acc_x**2 + acc_y**2 + acc_z**2)**0.5
                if total_acc > SHAKE_ACCELERATION_THRESHOLD:
                    print("Shake detected (pull pin)!")
                    call_speak_endpoint(server_base_url, 3)
                    current_state = State.AIM_NOZZLE
                    time.sleep(2)

            elif current_state == State.AIM_NOZZLE:
                if abs(imu.roll) < AIM_ANGLE_THRESHOLD:
                    print("Aiming detected!")
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