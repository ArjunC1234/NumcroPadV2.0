from components.RawInputReceiver import RawInputReceiver
from constants import LISTENER_FILE
import time


myReceiver = RawInputReceiver(LISTENER_FILE)

myReceiver.linkOnInput(lambda e: print(e))

myReceiver.start()

try:
    while myReceiver.is_running():
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Stopping...")
    myReceiver.stop()