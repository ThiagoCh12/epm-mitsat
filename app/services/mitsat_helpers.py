import datetime

_UTC_MINUS_3 = datetime.timezone(datetime.timedelta(hours=-3))


def to_utcminus3(dt: datetime.datetime) -> datetime.datetime:
    """Converte datetime (UTC ou naive) para UTC-3."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(_UTC_MINUS_3)


def format_datetime(dt: datetime.datetime) -> str:
    """Retorna string ISO 8601 em UTC-3, truncada para a hora cheia (mm:ss zerados)."""
    local = to_utcminus3(dt)
    return local.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")


def generate_message_id(station_id: int, timestamp: datetime.datetime) -> str:
    """
    Gera um message_id único por estação e hora cheia (UTC-3).
    Formato: est{station_id}_{YYYYMMDD}_{HH}0000

    Exemplo: est315_20260406_100000
    """
    local = to_utcminus3(timestamp).replace(minute=0, second=0, microsecond=0)
    return f"est{station_id}_{local.strftime('%Y%m%d_%H%M%S')}"


def build_payload(station_id: int, readings: list) -> dict:
    """
    Constrói o payload para POST /data-station/{station_id}.

    Args:
        station_id: ID da estação
        readings: lista de tuplas (timestamp_utc: datetime, value: float, type: int)

    Agrupa as leituras por instante de tempo em blocos de mensagem,
    cada um com um message_id único gerado a partir da estação e do timestamp.

    Returns:
        dict com chaves 'station_id' e 'data' (lista de blocos)
    """
    blocks: dict = {}

    for ts, value, msg_type in readings:
        msg_id = generate_message_id(station_id, ts)
        if msg_id not in blocks:
            blocks[msg_id] = {"message_id": msg_id, "message": []}
        blocks[msg_id]["message"].append({
            "type": msg_type,
            "date_time": format_datetime(ts),
            "value": value,
        })

    return {"station_id": station_id, "data": list(blocks.values())}
