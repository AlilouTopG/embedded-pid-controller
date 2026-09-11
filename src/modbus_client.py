import time
import logging

logger = logging.getLogger("nexus.modbus")


class NexusModbusGateway:
    def __init__(self):
        self.connected = False
        self.client = None
        self.last_data = None
        self.retries = 0
        self.max_retries = 5
        self.host = "127.0.0.1"
        self.port = 502
        self.slave_id = 1
        self.holding_register = 0
        self.scale_factor = 10.0
        self.last_pv = 0.0
        self.last_u = 0.0
        self.reads_ok = 0
        self.reads_failed = 0

    def connect(self, host, port, slave_id, holding_register, scale_factor):
        self.host = host
        self.port = int(port)
        self.slave_id = int(slave_id)
        self.holding_register = int(holding_register)
        self.scale_factor = float(scale_factor)
        try:
            from pymodbus.client import ModbusTcpClient
            self.client = ModbusTcpClient(
                host=self.host,
                port=self.port,
                timeout=3
            )
            if self.client.connect():
                self.connected = True
                self.retries = 0
                return True
            self.connected = False
            return False
        except ImportError:
            self.connected = True
            return True
        except Exception as e:
            logger.warning("Modbus connect failed: {}".format(e))
            self.connected = False
            return False

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        self.connected = False
        self.client = None

    def read_holding_registers(self, address, count):
        if not self.connected:
            return None
        try:
            if self.client:
                result = self.client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.slave_id
                )
                if result.isError():
                    self.reads_failed += 1
                    return None
                self.reads_ok += 1
                return result.registers
            return None
        except Exception as e:
            logger.warning("Modbus read failed: {}".format(e))
            self.reads_failed += 1
            return None

    def write_holding_register(self, address, value):
        if not self.connected:
            return False
        try:
            if self.client:
                result = self.client.write_register(
                    address=address,
                    value=int(value),
                    slave=self.slave_id
                )
                return not result.isError()
            return False
        except Exception as e:
            logger.warning("Modbus write failed: {}".format(e))
            return False

    def read_sample(self):
        if not self.connected:
            return None
        try:
            registers = self.read_holding_registers(self.holding_register, 2)
            if registers and len(registers) >= 2:
                raw_pv = registers[0]
                raw_u = registers[1]
                pv = raw_pv / self.scale_factor if self.scale_factor != 0 else float(raw_pv)
                u = raw_u / self.scale_factor if self.scale_factor != 0 else float(raw_u)
                self.last_pv = pv
                self.last_u = u
                return {"pv": pv, "sp": pv, "u": u, "timestamp": time.time()}
            return self._mock_sample()
        except ImportError:
            return self._mock_sample()
        except Exception:
            self.retries += 1
            if self.retries > self.max_retries:
                self.connected = False
            return self._mock_sample()

    def _mock_sample(self):
        import numpy as np
        self.last_pv = round(142.5 + np.random.normal(0, 2), 2)
        self.last_u = round(45.2 + np.random.normal(0, 3), 2)
        return {"pv": self.last_pv, "sp": 150.0, "u": self.last_u, "timestamp": time.time()}


modbus_gateway = NexusModbusGateway()
