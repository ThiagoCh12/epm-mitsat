"""
Utilitários de teste — execute com um argumento:

  python app/test_run.py epm      → lê a variável do EPM e exibe o último valor
  python app/test_run.py mitsat   → simula o ciclo completo enviando valor fixo à MITSAT
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import datetime as dt
import time

from app.main import logger, EPM_VARIABLE, VAZAO_TYPE, STATIONS, UTC_MINUS_3
from app.clients.epm_client import EpmClient
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


def test_epm() -> None:
    """Lê a variável do EPM e exibe o último valor da hora anterior."""
    now    = dt.datetime.now(dt.timezone.utc)
    fim    = now.replace(minute=0, second=0, microsecond=0)
    inicio = fim - dt.timedelta(hours=1)

    logger.info(f"[EPM] Lendo '{EPM_VARIABLE}' de {inicio} a {fim}")

    try:
        epm = EpmClient()
        data = epm.read_bv(EPM_VARIABLE, inicio, fim)
    except Exception as e:
        logger.error(f"[EPM] Falha: {e}")
        return

    if data is None or len(data) == 0:
        logger.warning("[EPM] Nenhum dado retornado para o período.")
        return

    last = data[-1]
    logger.info(f"[EPM] {len(data)} registros lidos.")
    logger.info(f"[EPM] Último valor: {float(last['Value'])} m³/s em {last['Timestamp']}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "mitsat"

    if mode == "epm":
        test_epm()
    elif mode == "mitsat":
        main()
    else:
        print("Uso: python app/test_run.py [epm|mitsat]")
