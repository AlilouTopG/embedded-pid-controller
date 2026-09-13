import logging
import time
from src.drivers.modbus_driver import IndustrialModbusClient
from tests.mock_plc import MockPLC

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IntegrationTest")


def run_test():
    logger.info("1. إطلاق محاكي الـ PLC كـ Daemon Thread...")
    plc = MockPLC(host="127.0.0.1", port=502)
    plc.start()
    time.sleep(1.0)  # مهلة لفتح مأخذ الشبكة (Socket)

    logger.info("2. إنشاء اتصال عميل Modbus TCP على المنفذ 502...")
    client = IndustrialModbusClient(host="127.0.0.1", port=502)
    connected = client.connect()

    if not connected:
        logger.error("❌ فشل الاتصال بخادم Modbus!")
        return

    logger.info("✅ تم الاتصال بالمحاكي بنجاح.")

    try:
        # اختبار كتابة خرج التحكم (MV/U = 80%) في السجل 1
        target_u = 80.0
        logger.info(f"3. إرسال أمر المشغل: U/MV = {target_u}%...")
        write_ok = client.write_mv(register_address=1, mv_percent=target_u)
        assert write_ok, "فشلت كتابة السجل!"
        logger.info("✅ تمت كتابة خرج التحكم بنجاح.")

        # مراقبة تطور واستجابة الحساس (PV) في السجل 0 على مدار 3 ثوانٍ
        logger.info("4. مراقبة ديناميكية استجابة الحساس (PV):")
        for step in range(6):
            time.sleep(0.5)
            pv_val = client.read_pv(register_address=0)
            logger.info(f"   [t = {(step + 1) * 0.5:.1f}s] Process Value (PV) = {pv_val}%")

        logger.info("🎯 اكتمل اختبار الاتصال والتكامل بنجاح تام!")

    finally:
        client.disconnect()


if __name__ == "__main__":
    run_test()
