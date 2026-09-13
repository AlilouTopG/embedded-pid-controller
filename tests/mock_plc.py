import time
import random
import socket
import struct
import threading


class MockPLC:
    def __init__(self, host="127.0.0.1", port=502):
        self.host = host
        self.port = port
        self.server = None
        self.running = False
        self.holding_registers = [0] * 100
        self.pv_base = 142.5
        self.pv_noise = 2.0
        self.pv = self.pv_base
        self.u = 0.0

    def start(self):
        self.running = True
        self.holding_registers[0] = int(self.pv_base * 10)
        self.holding_registers[1] = int(self.u * 10)
        self.server = threading.Thread(target=self._run_server, daemon=True)
        self.server.start()

    def stop(self):
        self.running = False

    def _run_server(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((self.host, self.port))
            sock.listen(1)
            sock.settimeout(1.0)
            while self.running:
                try:
                    conn, addr = sock.accept()
                    self._handle_client(conn)
                except socket.timeout:
                    continue
            sock.close()
        except Exception:
            self.running = False

    def _handle_client(self, conn):
        try:
            while self.running:
                data = conn.recv(1024)
                if not data:
                    break
                self._update_values()
                response = self._build_response(data)
                if response:
                    conn.sendall(response)
        except Exception:
            pass
        finally:
            conn.close()

    def _update_values(self):
        self.pv = self.pv_base + random.uniform(-self.pv_noise, self.pv_noise)
        self.holding_registers[0] = int(self.pv * 10)
        self.holding_registers[1] = int(self.u * 10)

    def _build_response(self, request):
        if len(request) < 8:
            return None
        func_code = request[1]
        if func_code == 3:
            reg_addr = struct.unpack(">H", request[2:4])[0]
            reg_count = struct.unpack(">H", request[4:6])[0]
            byte_count = reg_count * 2
            resp = bytearray()
            resp.extend(request[0:2])
            resp.append(func_code)
            resp.append(byte_count)
            for i in range(reg_count):
                idx = reg_addr + i
                if 0 <= idx < len(self.holding_registers):
                    resp.extend(struct.pack(">H", self.holding_registers[idx]))
                else:
                    resp.extend(struct.pack(">H", 0))
            return bytes(resp)
        elif func_code == 6:
            reg_addr = struct.unpack(">H", request[2:4])[0]
            reg_val = struct.unpack(">H", request[4:6])[0]
            if 0 <= reg_addr < len(self.holding_registers):
                self.holding_registers[reg_addr] = reg_val
            return request
        return None

    def set_register(self, address, value):
        if 0 <= address < len(self.holding_registers):
            self.holding_registers[address] = int(value)

    def get_register(self, address):
        if 0 <= address < len(self.holding_registers):
            return self.holding_registers[address]
        return 0


if __name__ == "__main__":
    plc = MockPLC()
    plc.start()
    print("MockPLC running on {}:{}".format(plc.host, plc.port))
    try:
        while True:
            time.sleep(1)
            plc._update_values()
            print("PV={:.1f} U={:.1f}".format(plc.pv, plc.u))
    except KeyboardInterrupt:
        plc.stop()
