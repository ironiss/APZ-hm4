from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from config import MESSAGES_SERVICE, LOGGING_SERVICE_PORTS

app = FastAPI()


class AvailableAPI(BaseModel):
    log_s: List[str]
    mes_s: List[str]


@app.get("/all_ports")
def handle() -> AvailableAPI:
    """
    Returns a static text.
    """

    all_appis = {
        "log_s": [f"http://" + "logging_service_" + str(port-5001) + ":" + str(port) for port in LOGGING_SERVICE_PORTS],
        "mes_s": ["http://message_service_1:5005",
            "http://message_service_2:5007"]
    }

    return all_appis

