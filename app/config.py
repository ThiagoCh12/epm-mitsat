from dotenv import load_dotenv
import os, datetime as dt

load_dotenv()

EPM_API      = os.getenv("EPM_API")
EPM_AUTH     = os.getenv("EPM_AUTH")
EPM_USER     = os.getenv("EPM_USER")
EPM_PASSWORD = os.getenv("EPM_PASSWORD")

MITSAT_BASE_URL = os.getenv("MITSAT_BASE_URL")
JUR_API_KEY     = os.getenv("JUR_API_KEY")
JUR_SECRET_KEY  = os.getenv("JUR_SECRET_KEY")

EPM_VARIABLE = os.getenv("EPM_VARIABLE")

STATIONS = {
    315: {
        "id": 315,
        "name": "UHE Juruena Barramento",
        "device_code": "ODLSKYF9C5",
        "company": "UHE Juruena S.A",
    }
}

VAZAO_TYPE     = 3
UTC_MINUS_3    = dt.timezone(dt.timedelta(hours=-3))
RUN_OFFSET_MIN = 0   # minutos após a virada da hora para garantir que o EPM finalizou
