import uuid
import httpx
import asyncio
import logging
import random
import json

from typing import Dict, Union, List

from fastapi import FastAPI
from pydantic import BaseModel

from aiokafka import AIOKafkaProducer

producer = None

app = FastAPI()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@app.on_event("startup")
async def startup_event():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=["kafka1:9092", "kafka2:9093", "kafka3:9094"]
    )
    await producer.start()

@app.on_event("shutdown")
async def shutdown_kafka_producer():
    if producer:
        await producer.stop()

class MessageRequestQuery(BaseModel):
    msg: str

class MessageResponseQuery(BaseModel):
    all_msgs: str


class AvailableAPI(BaseModel):
    log_s: List[str]
    mes_s: List[str]


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/send_to_logging_service")
async def generate_uuid(query: MessageRequestQuery) -> Dict[str, str]: 
    """
    Generating UUID for message and sending to the logging-service.
    HTTP POST to the loggining service with query: {UUID (str), msg(str)}

    Args:
        query (.msg (str)) -- message from the client
    Returns:
        {"status": "<status code>"}
    """

    unique_id = str(uuid.uuid4())
    data_query = {"UUID": unique_id, "msg": query.msg}

    async with httpx.AsyncClient() as client:
        response = await client.get(url=f"http://config_service:5006/all_ports")
        all_ports: AvailableAPI = AvailableAPI(**response.json())

        log_ports = all_ports.log_s
        random.shuffle(log_ports)

        for port in log_ports:
            for num in range(5):
                try:
                    response = await client.post(url=f"{port}/fetching_message", json=data_query)

                    await producer.send_and_wait("message-topic", json.dumps(data_query).encode("utf-8"))
                   
                    if response.status_code == 200:
                        logging.info(f"Try number {num} is successful")
                        return {"status": str(response.status_code)}
                except httpx.RequestError as e:
                    logging.info(f"Try number {num}, error: {str(e)}")
                    await asyncio.sleep(10)
        

    return {"status": "500"}

  
@app.get("/get_resulted_messages")
async def get_messages() -> Union[MessageResponseQuery, Dict[str, str]]:
    """
    Gets all messages that was saved by logging-service.

    Args:
        None
    Returns:
        {"all_msgs": "<all messages from loggining service separated by ',' and from message service separated by '\n'>"}
        or 
        {"status": "<status code>"} if errors occured
    """
    final_answer = True

    async with httpx.AsyncClient() as client:
        response = await client.get(url=f"http://config_service:5006/all_ports")
        all_ports: AvailableAPI = AvailableAPI(**response.json())

        log_ports = all_ports.log_s
        random.shuffle(log_ports)

        for port in log_ports:            
            try:
                all_messages_response = await client.get(url=f"{port}/get_fetched_messages")
                final_answer = True
                if all_messages_response.status_code == 200:
                    break
            except httpx.RequestError as _:
                final_answer = False
                continue
        
        message_services = all_ports.mes_s
        random_message_service = random.choice(message_services)

        static_text_response = await client.get(url=f"{random_message_service}/message_handler")
        
        if not final_answer:
            return {"status": "500"}
        elif static_text_response.status_code != 200:
            return {"status": static_text_response.status_code}
        
    all_messages_json = all_messages_response.json()
    static_text_json = static_text_response.json()

    response = all_messages_json["msgs"] + "\n" + static_text_json["static_text"]
    return {"all_msgs": response}
