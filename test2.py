import socket
import json

LISTENER_PORT = 5005

def main():
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow reuse of address, useful for testing on the same machine
    listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to all available interfaces
    listener_socket.bind(('', LISTENER_PORT))

    print(f"Listening for UDP broadcasts on port {LISTENER_PORT}...")

    while True:
        try:
            data, addr = listener_socket.recvfrom(4096) # Buffer size 4096 bytes
            decoded_data = data.decode('utf-8')
            try:
                json_data = json.loads(decoded_data)
                print(f"\n--- Received from {addr[0]} ---")
                print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                print(f"Received non-JSON data from {addr[0]}: {decoded_data}")
        except KeyboardInterrupt:
            print("\nListener stopped.")
            break
        except Exception as e:
            print(f"Error receiving data: {e}")

if __name__ == "__main__":
    main()