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
    Handles raw input events received from the Raspberry Pi broadcaster.
    Captures one key if mapping is active, otherwise runs turbo/macro logic as normal.
    """

    print(event)
    # --- IMPORTANT: Adapt to the new JSON structure from Raspberry Pi ---
    # The Pi script sends: {"device": {...}, "event": {...}}
    # We need to extract data from the 'event' and 'device' sub-dictionaries.

    # Extract event details
    event_details = event.get("event", {})
    key = event_details.get("keyname", "").lower()
    event_action = event_details.get("action") # This will be "press", "release", "hold", "move", etc.

    # Extract device details
    device_info = event.get("device", {})
    # For device_path, we need a unique identifier. A combination of VID, PID, and Product Name is good.
    # If VID/PID are still null, just use product_name.
    device_vid = device_info.get("vid", "unknown_vid")
    device_pid = device_info.get("pid", "unknown_pid")
    device_product_name = device_info.get("product_name", "Unknown Device").replace(" ", "_").replace("-", "_") # Sanitize for path-like use

    # Create a unique device identifier string for mapping/filtering
    # This will look like "046d_c077_Logitech_USB_Receiver" or "unknown_vid_unknown_pid_Unknown_Device"
    device_path_identifier = f"{device_vid}_{device_pid}_{device_product_name}"
    device_display_name = device_info.get("product_name", "Unknown Device") # For user-friendly display

    # --- End of Adaptation ---


    # -- KEY MAPPING MODE (capture one key and exit) --
    if parent.mapping_key_process:
        # We only want to capture actual key presses/releases, not movements or other event types
        if event_action not in ["press", "release"]:
            print(f"Skipping non-key event during mapping: {event_action}")
            return

        parent.mapping_key_process = False  # disable mapping mode after first *valid* event

        vb = getattr(parent, "mapping_target", None)
        if vb is None:
            parent.update_info_label.emit("Error: No virtual button selected for mapping.")
            return

        vb.mapped_key = key
        # Store the unique device identifier
        vb.set_mapped_device_path(device_path_identifier)

        # Save the device name for debug/display purposes
        vb.mapped_device = {"name": device_display_name} # Store the user-friendly name

        parent.update_info_label.emit(f"Mapped '{key}' from '{device_display_name}' to virtual button '{vb.name}'.")
        parent.mapping_target = None
        # Assuming macro_logic.update_macro_info exists and is accessible
        # You might need to adjust this call if macro_logic is not directly available
        # or if it expects a different object.
        # For now, assuming it's imported or passed correctly.
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

        # Device filtering based on the new unique identifier
        if parent.settings.get("device_filtering", False):
            if not vb.device_path: # If a VB has no device path mapped, it matches any device if filtering is off
                continue # If filtering is on, and no device path is mapped, it won't match.
            if vb.device_path != device_path_identifier: # Compare with the new unique identifier
                continue

        matched_vbs.append(vb)

    if not matched_vbs:
        return

    # Use event_action ("press", "release") instead of "down"/"up"
    if event_action == "press":
        if key in parent.pressed_keys:
            return
        parent.pressed_keys.add(key)

        for vb in matched_vbs:
            parent.highlight_signal.emit(vb, True)

            if vb.turbo_enabled:
                if not hasattr(parent, "turbo_threads"):
                    parent.turbo_threads = {}

                def turbo_runner(vb_obj, stop_event_obj): # Renamed args to avoid confusion with outer scope
                    delay = vb_obj.turbo_delay_ms / 1000.0
                    while not stop_event_obj.is_set():
                        if vb_obj.assigned_macro_id:
                            # Assuming run_macro is accessible
                            run_macro(parent, vb_obj.assigned_macro_id)
                        if stop_event_obj.wait(delay):
                            break

                stop_event = threading.Event()
                thread = threading.Thread(target=turbo_runner, args=(vb, stop_event), daemon=True)
                parent.turbo_threads[key] = (thread, stop_event)
                thread.start()

            elif vb.assigned_macro_id:
                # Assuming run_macro is accessible
                run_macro(parent, vb.assigned_macro_id)

    elif event_action == "release":
        if key in parent.pressed_keys:
            parent.pressed_keys.remove(key)

            for vb in matched_vbs:
                parent.highlight_signal.emit(vb, False)

            if hasattr(parent, "turbo_threads") and key in parent.turbo_threads:
                thread, stop_event = parent.turbo_threads.pop(key)
                stop_event.set()