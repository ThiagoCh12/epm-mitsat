import logging
import math
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from app.config import MITSAT_BASE_URL, JUR_API_KEY, JUR_SECRET_KEY
from app.services.mitsat_helpers import build_payload

logger = logging.getLogger("epm-mitsat")

_MAX_RETRIES  = 3
_RETRY_DELAYS = [5, 15, 45] 


class MitsatClient:

    def __init__(self):
        self.base_url   = MITSAT_BASE_URL
        self.client_key = JUR_API_KEY
        self.key_secret = JUR_SECRET_KEY
        self._token        = None
        self._token_expiry = None

    def _authenticate(self) -> bool:
        url     = f"{self.base_url}/client/login-key"
        payload = {"client_key": self.client_key, "key_secret": self.key_secret}
        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()

            self._token = data.get("access_token") or data.get("token")
            if not self._token:
                logger.error("Token não encontrado na resposta de autenticação.")
                return False

            expires_in         = data.get("expires_in", 36000)
            self._token_expiry = datetime.now(timezone.utc).timestamp() + expires_in - 60
            logger.info(f"Autenticado na MITSAT (expira em {expires_in / 3600:.1f}h).")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Falha na autenticação MITSAT: {e}")
            return False

    def _ensure_authenticated(self) -> bool:
        if self._token and self._token_expiry:
            if datetime.now(timezone.utc).timestamp() < self._token_expiry:
                return True
        return self._authenticate()
    
    def _do_post(self, url: str, headers: dict, payload: dict) -> requests.Response:
        """POST com retry em falhas de conexão."""
        last_exc = None
        for attempt, delay in enumerate(_RETRY_DELAYS, 1):
            try:
                return requests.post(url, headers=headers, json=payload, timeout=30)
            except requests.exceptions.RequestException as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    logger.warning(f"POST tentativa {attempt}/{_MAX_RETRIES} falhou ({e}). Aguardando {delay}s...")
                    time.sleep(delay)
        raise last_exc

    def _do_get(self, url: str, headers: dict, params: dict = None) -> requests.Response:
        """GET com retry em falhas de conexão."""
        last_exc = None
        for attempt, delay in enumerate(_RETRY_DELAYS, 1):
            try:
                return requests.get(url, headers=headers, params=params, timeout=30)
            except requests.exceptions.RequestException as e:
                last_exc = e
                if attempt < _MAX_RETRIES:
                    logger.warning(f"GET tentativa {attempt}/{_MAX_RETRIES} falhou ({e}). Aguardando {delay}s...")
                    time.sleep(delay)
        raise last_exc

    def _authorized_post(self, url: str, payload: dict) -> Optional[requests.Response]:
        if not self._ensure_authenticated():
            return None

        headers  = {"Authorization": f"Bearer {self._token}"}
        response = self._do_post(url, headers, payload)

        if response.status_code == 401:
            logger.warning("Token rejeitado (401). Reautenticando...")
            if not self._authenticate():
                return None
            headers["Authorization"] = f"Bearer {self._token}"
            response = self._do_post(url, headers, payload)

        if response.status_code == 409:
            detail   = response.json().get("detail", {})
            saved    = len(detail.get("saved", []))
            partial  = len(detail.get("partial", []))
            conflict = len(detail.get("message_conflict", []))
            logger.warning(f"409 — {saved} salvos, {partial} parciais, {conflict} duplicados.")
            return response

        if response.status_code >= 400:
            try:
                logger.error(f"Erro HTTP {response.status_code}: {response.json()}")
            except Exception:
                logger.error(f"Erro HTTP {response.status_code}: {response.text}")

        response.raise_for_status()
        return response

    def _authorized_get(self, url: str, params: dict = None) -> Optional[requests.Response]:
        if not self._ensure_authenticated():
            return None

        headers  = {"Authorization": f"Bearer {self._token}"}
        response = self._do_get(url, headers, params)

        if response.status_code == 401:
            logger.warning("Token rejeitado (401). Reautenticando...")
            if not self._authenticate():
                return None
            headers["Authorization"] = f"Bearer {self._token}"
            response = self._do_get(url, headers, params)

        response.raise_for_status()
        return response

    def post_data(self, station_id: int, readings: list, chunk_size: int = 500) -> bool:
        """
        Envia leituras hidrológicas em lotes.

        Args:
            station_id: ID da estação cadastrada na MITSAT
            readings:   lista de (timestamp_utc: datetime, value: float, type: int)
            chunk_size: registros por requisição (padrão 500)

        Returns:
            True se todos os lotes foram aceitos, False caso contrário.
        """
        url   = f"{self.base_url}/data-station"
        total = len(readings)
        total_batches = math.ceil(total / chunk_size)
        sent_blocks   = 0

        for batch_num, i in enumerate(range(0, total, chunk_size), 1):
            chunk   = readings[i:i + chunk_size]
            payload = build_payload(station_id, chunk)

            try:
                response = self._authorized_post(url, payload)
                if response is None:
                    return False
                sent_blocks += len(payload["data"])
                logger.info(
                    f"[{station_id}] Lote {batch_num}/{total_batches}: "
                    f"{len(payload['data'])} blocos enviados [HTTP {response.status_code}]."
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"[{station_id}] Falha no lote {batch_num}/{total_batches}: {e}")
                return False

        logger.info(f"[{station_id}] Total: {sent_blocks} blocos enviados.")
        return True

    def list_stations(self):
        """Lista as estações associadas à conta autenticada."""
        url = f"{self.base_url}/client/station"
        try:
            r = self._authorized_get(url)
            return r.json() if r else None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao listar estações: {e}")
            return None
