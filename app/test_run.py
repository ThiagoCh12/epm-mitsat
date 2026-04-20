"""
Utilitários de teste — execute com um argumento:

  python app/test_run.py epm      → lê a variável do EPM e exibe o último valor
  python app/test_run.py mitsat   → lê o EPM e envia o último valor na hora cheia atual (execução única)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import datetime as dt

from app.main import logger, EPM_VARIABLE, VAZAO_TYPE, STATIONS, UTC_MINUS_3
from app.clients.epm_client import EpmClient
from app.clients.mitsat_client import MitsatClient


def test_epm() -> None:
    """Lê a variável do EPM e exibe o último valor da hora atual."""
    now    = dt.datetime.now(dt.timezone.utc)
    inicio = now.replace(minute=0, second=0, microsecond=0)

    logger.info(f"[EPM] Lendo '{EPM_VARIABLE}' de {inicio} a {now}")

    try:
        epm  = EpmClient()
        data = epm.read_bv(EPM_VARIABLE, inicio, now)
    except Exception as e:
        logger.error(f"[EPM] Falha: {e}")
        return

    if data is None or len(data) == 0:
        logger.warning("[EPM] Nenhum dado retornado para o período.")
        return

    last = data[-1]
    logger.info(f"[EPM] {len(data)} registros lidos.")
    logger.info(f"[EPM] Último valor: {float(last['Value'])} m³/s em {last['Timestamp']}")


def test_mitsat() -> None:
    """Lê o último valor do EPM (hora atual) e envia para a MITSAT com timestamp HH:00:00."""
    now    = dt.datetime.now(dt.timezone.utc)
    inicio = now.replace(minute=0, second=0, microsecond=0)
    fim    = inicio  # timestamp de envio = hora cheia atual (ex: 10:00:00)

    logger.info("=" * 60)
    logger.info(f"[TESTE] Lendo '{EPM_VARIABLE}' de {inicio} a {now}")

    try:
        epm  = EpmClient()
        data = epm.read_bv(EPM_VARIABLE, inicio, now)
    except Exception as e:
        logger.error(f"[TESTE] Falha ao ler EPM: {e}")
        return

    if data is None or len(data) == 0:
        logger.warning("[TESTE] Nenhum dado retornado pelo EPM.")
        return

    last  = data[-1]
    value = float(last["Value"])
    logger.info(f"[TESTE] {len(data)} registros lidos. Último valor: {value} m³/s")
    logger.info(f"[TESTE] Enviando com timestamp: {fim.strftime('%Y-%m-%dT%H:%M:%S')} UTC → {fim.astimezone(UTC_MINUS_3).strftime('%H:%M:%S')} UTC-3")

    mitsat = MitsatClient()
    for station in STATIONS.values():
        sid  = station["id"]
        name = station["name"]
        logger.info(f"[TESTE][{sid}] {name} — enviando {value} m³/s")
        mitsat.post_data(sid, [(fim, value, VAZAO_TYPE)])

    logger.info("[TESTE] Envio finalizado.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode == "epm":
        test_epm()
    elif mode == "mitsat":
        test_mitsat()
    else:
        print("Uso: python app/test_run.py [epm|mitsat]")
