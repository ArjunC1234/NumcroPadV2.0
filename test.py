from components.RawInputReceiver import RawInputReceiver
from constants import LISTENER_FILE
import time

def handle_input(event):
    print("[Key Event]", event)

def main():
    print("Starting RawInputReceiver...")
    receiver = RawInputReceiver(
        exe_path=LISTENER_FILE
    )
    receiver.linkOnInput(handle_input)
    receiver.start()
    counter = 0
    try:
        while True:
            if (counter==10):
                print("enter numpad has been blocked ---------------------------------------")
                receiver.send_block_rules(
                    (r"\\?\HID#{00001124-0000-1000-8000-00805f9b34fb}_VID&000204e8_PID&7021&Col01#a&6265721&0&0000#{884b96c3-56ef-11d1-bc8c-00a0c91405dd}", 
                    "enter")
                )
            time.sleep(1)
            counter+=1
    except KeyboardInterrupt:
        print("\nStopping...")
        receiver.stop()

if __name__ == "__main__":
    main()