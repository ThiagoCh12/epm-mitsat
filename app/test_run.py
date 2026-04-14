"""
Simulação do main.py sem leitura do EPM.
Acorda a cada HH:00 e envia um valor fixo para todas as estações.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import datetime as dt
import time

from app.main import logger, VAZAO_TYPE, STATIONS, UTC_MINUS_3
from app.clients.mitsat_client import MitsatClient

TEST_VALUE   = 42.00
RUN_OFFSET_MIN = 0   # acorda exatamente no HH:00 (main usa 5)


def seconds_until_next_run() -> float:
    now      = dt.datetime.now(UTC_MINUS_3)
    next_run = now.replace(minute=RUN_OFFSET_MIN, second=0, microsecond=0)
    if next_run <= now:
        next_run += dt.timedelta(hours=1)
    return (next_run - now).total_seconds()


def run_cycle() -> None:
    now = dt.datetime.now(UTC_MINUS_3)
    fim = now.replace(minute=0, second=0, microsecond=0)

    logger.info("=" * 60)
    logger.info(f"[TESTE] Ciclo iniciado — timestamp de envio: {fim.strftime('%Y-%m-%d %H:%M UTC-3')}")

    mitsat = MitsatClient()

    for station in STATIONS.values():
        sid  = station["id"]
        name = station["name"]
        logger.info(f"[TESTE][{sid}] {name} — enviando {TEST_VALUE} m³/s")
        mitsat.post_data(sid, [(fim, TEST_VALUE, VAZAO_TYPE)])

    logger.info("[TESTE] Ciclo finalizado.")


def main() -> None:
    logger.info("EPM→MITSAT [MODO TESTE] iniciado.")

    while True:
        wait    = seconds_until_next_run()
        next_dt = dt.datetime.now(UTC_MINUS_3) + dt.timedelta(seconds=wait)
        logger.info(f"[TESTE] Próximo ciclo em {wait / 60:.1f} min ({next_dt.strftime('%H:%M UTC-3')})")
        time.sleep(wait)
        run_cycle()


if __name__ == "__main__":
    main()
