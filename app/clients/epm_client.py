import logging
import datetime

import epmwebapi as epm
from epmwebapi import QueryPeriod
import numpy as np
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.config import EPM_AUTH, EPM_PASSWORD, EPM_USER, EPM_API

logger = logging.getLogger("epm-mitsat")


class EpmClient:

    def __init__(self):
        self.epm_auth     = EPM_AUTH
        self.epm_api      = EPM_API
        self.epm_user     = EPM_USER
        self.epm_password = EPM_PASSWORD
        self.con          = self._login()

    def _login(self):
        con = epm.EpmConnection(
            self.epm_auth,
            self.epm_api,
            self.epm_user,
            self.epm_password
        )
        if not con:
            raise ConnectionError("Falha ao estabelecer conexão com o EPM.")
        logger.info("Conexão com EPM WEB API estabelecida.")
        return con

    def read_bv(self, name: str, inicio: datetime.datetime, fim: datetime.datetime):
        bv = self.con.getBasicVariables(name)
        query_period = QueryPeriod(inicio, fim)
        return bv[name].historyReadRaw(queryPeriod=query_period, bounds=False)

    def write_bv(self, name: str, timestamps, values, qualities=None):
        bv = self.con.getBasicVariables(name)
        if qualities is None:
            qualities = [0] * len(values)

        dtype = np.dtype([
            ('Value',     '>f4'),
            ('Timestamp', 'object'),
            ('Quality',   'object'),
        ])
        data = np.empty(len(values), dtype=dtype)
        data['Value']     = values
        data['Timestamp'] = timestamps
        data['Quality']   = qualities

        bv[name].historyUpdate(data)
        logger.info(f"Dados inseridos com sucesso em '{name}'.")
