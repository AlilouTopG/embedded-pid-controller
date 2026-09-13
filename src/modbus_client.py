import logging
import time
from typing import List, Optional, Tuple
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModbusClient")


class IndustrialModbusClient:
    """Industrial Modbus TCP Driver for PLC/PAC Interfacing."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5020,
        timeout: float = 1.0,
        raw_scale_range: Tuple[int, int] = (0, 27648),
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.raw_min, self.raw_max = raw_scale_range
        self.client: Optional[ModbusTcpClient] = None
        self.is_connected = False
        self.last_latency_ms = 0.0

    def connect(self) -> bool:
        """فتح اتصال مقبس الشبكة مع الـ PLC."""
        try:
            self.client = ModbusTcpClient(self.host, port=self.port, timeout=self.timeout)
            self.is_connected = self.client.connect()
            return self.is_connected
        except Exception as e:
            logger.error(f"Modbus connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """إغلاق الاتصال بأمان."""
        if self.client:
            self.client.close()
            self.is_connected = False

    def read_holding_registers(self, start_address: int = 0, count: int = 5) -> Tuple[Optional[List[int]], float]:
        """قراءة كتلة من سجلات الـ Holding وحساب زمن الذهاب والإياب (RTT Latency)."""
        if not self.is_connected:
            if not self.connect():
                return None, 0.0

        t0 = time.perf_counter()
        try:
            result = self.client.read_holding_registers(address=start_address, count=count, slave=1)
            self.last_latency_ms = (time.perf_counter() - t0) * 1000.0
            if result.isError():
                return None, self.last_latency_ms
            return result.registers, self.last_latency_ms
        except ModbusException:
            self.is_connected = False
            return None, 0.0

    def read_pv(self, register_address: int = 0) -> Optional[float]:
        """قراءة المتغير المقاس (PV) من السجل المحدد وتحويله إلى نسبة مئوية (0 - 100%)."""
        regs, _ = self.read_holding_registers(start_address=register_address, count=1)
        if regs:
            raw_val = max(self.raw_min, min(self.raw_max, regs[0]))
            pv_pct = ((raw_val - self.raw_min) / (self.raw_max - self.raw_min)) * 100.0
            return round(pv_pct, 2)
        return None

    def write_mv(self, register_address: int = 1, mv_percent: float = 0.0) -> bool:
        """كتابة أمر التحكم (MV) في سجل المشغل."""
        if not self.is_connected:
            if not self.connect():
                return False

        try:
            bounded_mv = max(0.0, min(100.0, mv_percent))
            raw_val = int(self.raw_min + (bounded_mv / 100.0) * (self.raw_max - self.raw_min))
            res = self.client.write_register(address=register_address, value=raw_val, slave=1)
            return not res.isError()
        except ModbusException:
            self.is_connected = False
            return False