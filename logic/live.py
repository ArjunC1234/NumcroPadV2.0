import time
import keyboard
import threading
import pywinusb.hid as hid

import logic.table as table_logic
import logic.macros as macro_logic

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


def on_raw_input(parent, event):
    """
    Handles raw input events. Captures one key if mapping is active,
    otherwise runs turbo/macro logic as normal.
    """
    key = event.get("keyName", "").lower()
    event_type = event.get("eventType")
    device_path = event.get("device")
    device_name = event.get("product", "Unknown Device")

    # -- KEY MAPPING MODE (capture one key and exit) --
    if parent.mapping_key_process:
        parent.mapping_key_process = False  # disable mapping mode after first event

        vb = getattr(parent, "mapping_target", None)
        if vb is None:
            parent.info_label.setText("Error: No virtual button selected for mapping.")
            return

        vb.mapped_key = key
        vb.set_mapped_device_path(device_path)

        # Save the device name for debug/display purposes
        vb.mapped_device = {"name": device_name}

        parent.info_label.setText(f"Mapped '{key}' from '{device_name}' to virtual button '{vb.name}'.")
        parent.mapping_target = None
        macro_logic.update_macro_info(parent, vb)
        parent.key_mapped_signal.emit()
        return

    # -- NORMAL LISTENING MODE --
    if not hasattr(parent, "pressed_keys"):
        parent.pressed_keys = set()

    matched_vbs = []
    for vb in parent.virtual_buttons:
        if vb.mapped_key != key:
            continue

        if parent.settings.get("device_filtering", False):
            if not vb.device_path:
                continue
            if vb.device_path != device_path:
                continue

        matched_vbs.append(vb)

    if not matched_vbs:
        return

    if event_type == "down":
        if key in parent.pressed_keys:
            return
        parent.pressed_keys.add(key)

        for vb in matched_vbs:
            parent.highlight_signal.emit(vb, True)

            if vb.turbo_enabled:
                if not hasattr(parent, "turbo_threads"):
                    parent.turbo_threads = {}

                def turbo_runner(vb, stop_event):
                    delay = vb.turbo_delay_ms / 1000.0
                    while not stop_event.is_set():
                        if vb.assigned_macro_id:
                            run_macro(parent, vb.assigned_macro_id)
                        if stop_event.wait(delay):
                            break

                stop_event = threading.Event()
                thread = threading.Thread(target=turbo_runner, args=(vb, stop_event), daemon=True)
                parent.turbo_threads[key] = (thread, stop_event)
                thread.start()

            elif vb.assigned_macro_id:
                run_macro(parent, vb.assigned_macro_id)

    elif event_type == "up":
        if key in parent.pressed_keys:
            parent.pressed_keys.remove(key)

            for vb in matched_vbs:
                parent.highlight_signal.emit(vb, False)

            if hasattr(parent, "turbo_threads") and key in parent.turbo_threads:
                thread, stop_event = parent.turbo_threads.pop(key)
                stop_event.set()
