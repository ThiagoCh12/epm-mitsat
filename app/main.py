"""
EPM → MITSAT  |  Sincronização horária de vazão de defluência.

Roda continuamente, executando um ciclo a cada hora (HH:05 UTC-3).
A cada ciclo lê a hora anterior do EPM e envia para a MITSAT.
"""

import os
import sys
import datetime as dt
import logging
import time
import urllib3
from logging.handlers import TimedRotatingFileHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.clients.epm_client import EpmClient
from app.clients.mitsat_client import MitsatClient
from app.config import STATIONS

# ── Constantes ────────────────────────────────────────────────────────────────

EPM_VARIABLE   = "JUR_TA_Med_VazDefl"
VAZAO_TYPE     = 3
UTC_MINUS_3    = dt.timezone(dt.timedelta(hours=-3))
RUN_OFFSET_MIN = 5   # minutos após a virada da hora para garantir que o EPM finalizou

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("epm-mitsat")
logger.setLevel(logging.INFO)

# Arquivo — rotação diária, retém 30 dias
_fh = TimedRotatingFileHandler(
    os.path.join(LOG_DIR, "epm_mitsat.log"),
    when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
_fh.setFormatter(_fmt)
logger.addHandler(_fh)

# Console
_ch = logging.StreamHandler()
_ch.setFormatter(_fmt)
logger.addHandler(_ch)

# ── Lógica de ciclo ───────────────────────────────────────────────────────────

def previous_hour_window() -> tuple[dt.datetime, dt.datetime]:
    """Retorna (inicio, fim) da hora anterior completa em UTC.
    Exemplo: acorda às 11:05 → retorna (10:00, 11:00).
    O último valor dessa janela é enviado com timestamp truncado para 10:00:00.
    """
    now    = dt.datetime.now(dt.timezone.utc)
    fim    = now.replace(minute=0, second=0, microsecond=0)
    inicio = fim - dt.timedelta(hours=1)
    return inicio, fim


def seconds_until_next_run() -> float:
    """Segundos até HH:05 da próxima hora (UTC-3)."""
    now      = dt.datetime.now(UTC_MINUS_3)
    next_run = now.replace(minute=RUN_OFFSET_MIN, second=0, microsecond=0)
    if next_run <= now:
        next_run += dt.timedelta(hours=1)
    return (next_run - now).total_seconds()


def process_station(
    epm_client: EpmClient,
    mitsat: MitsatClient,
    station: dict,
    inicio: dt.datetime,
    fim: dt.datetime,
) -> bool:
    sid  = station["id"]
    name = station["name"]

    logger.info(f"[{sid}] {name} — lendo '{EPM_VARIABLE}' de {inicio} a {fim}")

    try:
        data = epm_client.read_bv(EPM_VARIABLE, inicio, fim)
    except Exception as e:
        logger.error(f"[{sid}] Falha ao ler EPM: {e}")
        return False

    if data is None or len(data) == 0:
        logger.warning(f"[{sid}] Nenhum dado retornado pelo EPM para o período.")
        return False

    last  = data[-1]
    value = float(last["Value"])
    logger.info(f"[{sid}] {len(data)} registros lidos. Último valor: {value} m³/s → enviando com timestamp {fim}")

    return mitsat.post_data(sid, [(fim, value, VAZAO_TYPE)])


def run_cycle() -> None:
    inicio, fim = previous_hour_window()
    logger.info(f"{'='*60}")
    logger.info(f"Ciclo iniciado: {inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%H:%M')} UTC")

    try:
        epm_client = EpmClient()
    except Exception as e:
        logger.error(f"Não foi possível conectar ao EPM: {e}")
        return

    mitsat = MitsatClient()

    for station in STATIONS.values():
        try:
            process_station(epm_client, mitsat, station, inicio, fim)
        except Exception as e:
            logger.error(f"[{station['id']}] Erro inesperado: {e}", exc_info=True)

    logger.info("Ciclo finalizado.")


# ── Entrypoint ────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("EPM→MITSAT iniciado.")
    logger.info(f"Estações configuradas: {[s['name'] for s in STATIONS.values()]}")

    while True:
        wait    = seconds_until_next_run()
        next_dt = dt.datetime.now(UTC_MINUS_3) + dt.timedelta(seconds=wait)
        logger.info(f"Próximo ciclo em {wait / 60:.1f} min ({next_dt.strftime('%H:%M UTC-3')})")
        time.sleep(wait)
        run_cycle()


if __name__ == "__main__":
    main()
