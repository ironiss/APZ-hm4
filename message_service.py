from fastapi import FastAPI
from pydantic import BaseModel
from aiokafka import AIOKafkaConsumer

import json
import asyncio
import socket

app = FastAPI()

bootstrap_server = 'localhost:9092'
topicName = 'apz-messages'
messages = []

def json_deserializer(serialized):
    if serialized is None:
        return None
    json.loads(serialized)

class MessageFedaultHandler(BaseModel):
    static_text: str

async def consume():
    consumer_id = socket.gethostname()

    consumer = AIOKafkaConsumer(
        "message-topic",
        bootstrap_servers=["kafka1:9092", "kafka2:9093", "kafka3:9094"],
        group_id="message-group",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))

            print(f"Starting consumer {consumer_id} with message: {data['msg']}")
            messages.append(f'{data["msg"]}')
    finally:
        await consumer.stop()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.on_event("startup")
async def startup():
    asyncio.create_task(consume())

@app.get("/message_handler")
async def handle() -> MessageFedaultHandler:
    return {"static_text": ", ".join(messages)}

