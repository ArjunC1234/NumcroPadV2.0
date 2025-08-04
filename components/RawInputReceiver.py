import threading
import json
import socket
import queue
import sys
import traceback
from PyQt5 import QtCore


# === Global Exception Hook ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("[Global Error]", "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

sys.excepthook = handle_exception


# === Thread Safety Wrapper ===
def safe_thread_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"[Thread Error] {func.__name__}: {e}\n{traceback.format_exc()}")
    return wrapper


class RawInputReceiver(QtCore.QObject):
    """
    Multi-client TCP server + UDP discovery responder.
    Safely communicates with PyQt using signals.
    """
    raw_input_signal = QtCore.pyqtSignal(dict)  # Emits parsed events to main thread
    status_signal = QtCore.pyqtSignal(str)  # ✅ NEW
    def __init__(self, listen_port=5005, discovery_port=5006):
        super().__init__()
        self.listen_port = listen_port
        self.discovery_port = discovery_port
        self.server_socket = None
        self.discovery_socket = None
        self.active_clients = {}
        self._running = False
        self.event_queue = queue.Queue()

        self.server_thread = None
        self.discovery_thread = None
        self.processor_thread = None

        print(f"[RawInputReceiver] Initialized on TCP {listen_port}, UDP {discovery_port}")

    # === Start/Stop Methods ===
    def start(self):
        if self._running:
            print("[RawInputReceiver] Already running.")
            return

        try:
            # TCP server setup
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.listen_port))
            self.server_socket.listen(5)

            # UDP discovery setup
            self.discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.discovery_socket.bind(('', self.discovery_port))
            self.discovery_socket.settimeout(1.0)

            self._running = True

            # Threads
            self.server_thread = threading.Thread(
                target=safe_thread_wrapper(self._server_loop), daemon=True)
            self.discovery_thread = threading.Thread(
                target=safe_thread_wrapper(self._discovery_listener_loop), daemon=True)
            self.processor_thread = threading.Thread(
                target=safe_thread_wrapper(self._process_events_loop), daemon=True)

            self.server_thread.start()
            self.discovery_thread.start()
            self.processor_thread.start()

            print("[RawInputReceiver] Server started successfully.")

        except Exception as e:
            print(f"[RawInputReceiver] Startup Error: {e}\n{traceback.format_exc()}")
            self._running = False

    def stop(self):
        print("[RawInputReceiver] Stopping...")
        self._running = False

        # Close clients
        for addr, (conn, _) in list(self.active_clients.items()):
            try:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            except:
                pass
            self.active_clients.pop(addr, None)

        # Close sockets
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
                self.server_socket.close()
            except:
                pass
            self.server_socket = None

        if self.discovery_socket:
            try:
                self.discovery_socket.close()
            except:
                pass
            self.discovery_socket = None

        print("[RawInputReceiver] Waiting for threads to exit...")
        for t in [self.server_thread, self.discovery_thread, self.processor_thread]:
            if t and t.is_alive():
                t.join(timeout=2)

        print("[RawInputReceiver] Stopped.")

    # === Internal Threads ===
    def _server_loop(self):
        while self._running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                print(f"[RawInputReceiver] Client connected: {addr}")

                t = threading.Thread(
                    target=safe_thread_wrapper(self._handle_client),
                    args=(conn, addr),
                    daemon=True
                )
                self.active_clients[addr] = (conn, t)
                t.start()

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Server Loop Error] {e}\n{traceback.format_exc()}")

    def _handle_client(self, conn, addr):
        buffer = ""
        conn.settimeout(1.0)
        while self._running:
            try:
                data = conn.recv(4096)
                if not data:
                    break

                buffer += data.decode()
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            event = json.loads(line)
                            self.event_queue.put(event)
                        except json.JSONDecodeError:
                            print(f"[JSON Error] {line}")

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Client Handler Error] {e}\n{traceback.format_exc()}")
                break

        conn.close()
        self.active_clients.pop(addr, None)
        print(f"[RawInputReceiver] Client {addr} disconnected.")

    def _discovery_listener_loop(self):
        while self._running:
            try:
                data, addr = self.discovery_socket.recvfrom(1024)
                req = json.loads(data.decode())
                if req.get("type") == "discovery_request":
                    response = json.dumps({
                        "type": "discovery_response",
                        "sender": "windows_macro_app",
                        "ip_address": self._get_local_ip()
                    }).encode()
                    self.discovery_socket.sendto(response, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[Discovery Loop Error] {e}")

    def _process_events_loop(self):
        while self._running:
            try:
                event = self.event_queue.get(timeout=0.1)
                self.raw_input_signal.emit(event)  # Safe emit
                self.event_queue.task_done()
            except queue.Empty:
                continue

    def _get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def is_running(self):
        return self._running
