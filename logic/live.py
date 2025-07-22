import time
import keyboard
import threading
import pywinusb.hid as hid

import logic.table as table_logic

def handle_key_press(parent, key_str):
    parent.log_message(f"Pressed key: {key_str}")

    for vb in parent.virtual_buttons:
        if vb.physical_key == key_str:
            macro_id = vb.assigned_macro_id
            if macro_id and macro_id in parent.macros:
                macro = parent.macros[macro_id]
                run_macro(macro_id)
                parent.log_message(f"Macro '{macro['name']}' triggered by key '{key_str}'.")

def run_macro(parent, macro_id):
    if macro_id not in parent.macros:
        return
    macro = parent.macros[macro_id]

    def macro_thread():
        start_time = time.time()

        # Track all press/release events as (timestamp, action, key)
        events = []

        for step in macro.get("steps", []):
            key = step.get("key")
            delay = step.get("delay", 0)
            duration = step.get("duration", 0)

            if not key:
                continue

            press_time = start_time + delay
            release_time = press_time + duration

            events.append((press_time, "press", key))
            events.append((release_time, "release", key))

        # Sort all events by time
        events.sort(key=lambda e: e[0])

        for event_time, action, key in events:
            now = time.time()
            wait_time = event_time - now
            if wait_time > 0:
                time.sleep(wait_time)

            if action == "press":
                keyboard.press(key)
            else:  # release
                keyboard.release(key)

        parent.log_message(f"Macro '{macro.get('name','')}' executed.")

    threading.Thread(target=macro_thread, daemon=True).start()


def listen_to_keys(parent):
    parent.turbo_threads = {}  # key -> (thread, stop_event)

    def turbo_macro_runner(vb, stop_event):
        delay = vb.turbo_delay_ms / 1000.0
        while not stop_event.is_set():
            if vb.assigned_macro_id:
                print(f"[Turbo] Running macro {vb.assigned_macro_id} for {vb.name}")
                run_macro(vb.assigned_macro_id)
            if stop_event.wait(delay):
                break

    def on_key_event(e):
        key = keyboard.normalize_name(e.name or "")
        if not key:
            return True

        # Get device filtering setting
        device_filtering = parent.settings.get("device_filtering", False)
        matched_vbs = []

        for vb in parent.virtual_buttons:
            if vb.mapped_key != key:
                continue

            if device_filtering:
                # Skip if no mapped device info
                if not vb.mapped_device:
                    continue

                e_vid = getattr(e, "device", None)
                if not hasattr(e, "device") or e.device is None:
                    continue

                try:
                    device_info = e.device  # From keyboard module, might not match pywinusb info
                    # pywinusb does not provide easy access via keyboard events;
                    # you must use raw_handler or use keyboard's `device.name`
                    dev_str = str(device_info)
                    # Match as best effort using serial number substring or description
                    if not (
                        vb.mapped_device["serial_number"] in dev_str or
                        f"{vb.mapped_device['vendor_id']:04X}" in dev_str or
                        f"{vb.mapped_device['product_id']:04X}" in dev_str
                    ):
                        continue
                except Exception as ex:
                    print(f"[Warning] Could not filter device: {ex}")
                    continue

            matched_vbs.append(vb)

        if not matched_vbs:
            return True

        if key in parent.turbo_threads:
            if e.event_type == 'up':
                thread, stop_event = parent.turbo_threads.pop(key)
                stop_event.set()
                for vb in matched_vbs:
                    parent.highlight_signal.emit(vb, False)
                parent.pressed_keys.discard(key)
            return False

        if e.event_type == 'down':
            if key not in parent.pressed_keys:
                parent.pressed_keys.add(key)
                for vb in matched_vbs:
                    parent.highlight_signal.emit(vb, True)
                    if vb.turbo_enabled:
                        stop_event = threading.Event()
                        thread = threading.Thread(target=turbo_macro_runner, args=(vb, stop_event), daemon=True)
                        parent.turbo_threads[key] = (thread, stop_event)
                        thread.start()
                    elif vb.assigned_macro_id:
                        parent.run_macro(vb.assigned_macro_id)
            return False

        elif e.event_type == 'up':
            if key in parent.pressed_keys:
                parent.pressed_keys.remove(key)
                for vb in matched_vbs:
                    parent.highlight_signal.emit(vb, False)
            return False

        return True

    threading.Thread(target=lambda: keyboard.hook(on_key_event, suppress=True), daemon=True).start()

def listen_for_key(parent, virtual_button):
    """
    Wait for a single key press globally with 3 second timeout,
    then map it to the virtual button and store device info using pywinusb.
    """
    key_captured = {"done": False, "key": None}
    device_captured = {"device": None}

    # pywinusb handler to capture the originating device
    def raw_handler(data):
        if not device_captured["path"]:
            try:
                print(f"Raw data from: {data.device.vendor_name} - {data.device.product_name}")
                device_captured["path"] = data.device.device_path
            except Exception as e:
                print(f"Error capturing device: {e}")

    # Open all HID devices and set raw data handlers
    all_devices = hid.HidDeviceFilter().get_devices()
    for device in all_devices:
        try:
            device.open()
            device.set_raw_data_handler(raw_handler)
        except Exception as e:
            print(f"Failed to open/set handler for device: {e}")
            continue

    # Hook keyboard for key name
    def on_event(e):
        if e.event_type == "down":
            key_captured["key"] = e.name
            key_captured["done"] = True
            keyboard.unhook(hook)  # Unhook only this hook

    hook = keyboard.hook(on_event)

    # Wait for key press or timeout
    start_time = time.time()
    while not key_captured["done"] and (time.time() - start_time) < 3:
        time.sleep(0.01)

    # Cleanup HID devices
    for device in all_devices:
        try:
            device.set_raw_data_handler(None)
            device.close()
        except:
            continue

    # Store result
    if key_captured["done"]:
        virtual_button.mapped_key = key_captured["key"]

        if device_captured["device"]:
            virtual_button.set_mapped_device_from_pywinusb(device_captured["device"])
            dev_info = virtual_button.mapped_device
            dev_str = f"{dev_info['vendor_id']:04X}:{dev_info['product_id']:04X} - {dev_info['serial_number']}"
        else:
            virtual_button.mapped_device = None
            dev_str = "Unknown"

        parent.info_label.setText(
            f"Mapped '{key_captured['key']}' to virtual button '{virtual_button.name}'.\n"
            f"Device: {dev_str}"
        )
    else:
        parent.info_label.setText("No key pressed. Mapping cancelled.")

    table_logic.update_table(parent)