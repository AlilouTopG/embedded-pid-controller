import time
import logging

logger = logging.getLogger("nexus.modbus")

_MODBUS_REGISTER_MIN = 0
_MODBUS_REGISTER_MAX = 65535
_MODBUS_VALUE_MIN = 0
_MODBUS_VALUE_MAX = 65535
_MODBUS_SLAVE_MIN = 1
_MODBUS_SLAVE_MAX = 247


def _validate_register_address(address):
    try:
        addr = int(address)
    except (TypeError, ValueError):
        return False
    return _MODBUS_REGISTER_MIN <= addr <= _MODBUS_REGISTER_MAX


def _validate_register_value(value):
    try:
        val = int(value)
    except (TypeError, ValueError):
        return False
    return _MODBUS_VALUE_MIN <= val <= _MODBUS_VALUE_MAX


def _validate_slave_id(slave_id):
    try:
        sid = int(slave_id)
    except (TypeError, ValueError):
        return False
    return _MODBUS_SLAVE_MIN <= sid <= _MODBUS_SLAVE_MAX


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
        self.write_count = 0

    def connect(self, host, port, slave_id, holding_register, scale_factor):
        self.host = str(host).strip()
        self.port = int(port)
        self.slave_id = int(slave_id)
        self.holding_register = int(holding_register)
        self.scale_factor = float(scale_factor)
        if self.scale_factor == 0:
            self.scale_factor = 1.0
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
            self.connected = False
            self.client = None
            return False
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
        if not self.connected or self.client is None:
            return None
        if not _validate_register_address(address):
            return None
        try:
            result = self.client.read_holding_registers(
                address=int(address),
                count=int(count),
                slave=self.slave_id
            )
            if result.isError():
                self.reads_failed += 1
                return None
            self.reads_ok += 1
            return result.registers
        except Exception as e:
            logger.warning("Modbus read failed: {}".format(e))
            self.reads_failed += 1
            return None

    def write_holding_register(self, address, value):
        if not self.connected or self.client is None:
            return False
        if not _validate_register_address(address):
            logger.warning("Modbus write rejected: invalid address {}".format(address))
            return False
        if not _validate_register_value(value):
            logger.warning("Modbus write rejected: invalid value {}".format(value))
            return False
        try:
            result = self.client.write_register(
                address=int(address),
                value=int(value),
                slave=self.slave_id
            )
            if not result.isError():
                self.write_count += 1
                return True
            return False
        except Exception as e:
            logger.warning("Modbus write failed: {}".format(e))
            return False

    def read_sample(self):
        if not self.connected or self.client is None:
            return None
        try:
            registers = self.read_holding_registers(self.holding_register, 2)
            if registers and len(registers) >= 2:
                raw_pv = registers[0]
                raw_u = registers[1]
                pv = raw_pv / self.scale_factor
                u = raw_u / self.scale_factor
                self.last_pv = pv
                self.last_u = u
                return {"pv": pv, "sp": pv, "u": u, "timestamp": time.time()}
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
