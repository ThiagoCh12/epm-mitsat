from dotenv import load_dotenv
import os

load_dotenv()

EPM_API      = os.getenv("EPM_API")
EPM_AUTH     = os.getenv("EPM_AUTH")
EPM_USER     = os.getenv("EPM_USER")
EPM_PASSWORD = os.getenv("EPM_PASSWORD")

MITSAT_BASE_URL = os.getenv("MITSAT_BASE_URL")
JUR_API_KEY     = os.getenv("JUR_API_KEY")
JUR_SECRET_KEY  = os.getenv("JUR_SECRET_KEY")

STATIONS = {
    315: {
        "id": 315,
        "name": "UHE Juruena Barramento",
        "device_code": "ODLSKYF9C5",
        "company": "UHE Juruena S.A",
    }
}