import hazelcast

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

client = hazelcast.HazelcastClient(cluster_name="dev", cluster_members=["hazelcast_node_1:5701", "hazelcast_node_2:5701", "hazelcast_node_3:5701"])
msg_map = client.get_map("messages").blocking()

class MessageRequestQuery(BaseModel):
    UUID: str
    msg: str

class MessageResponseQuery(BaseModel):
    msgs: str


@app.post("/fetching_message")
def fulfill_hash_table(query: MessageRequestQuery) -> Dict[str, str]:
    """
    Saves messages to the Hash Table with key as uuid and value -- message.

    Args:
        query (.UUID (str)) -- unique identificator of message.
        query (.msg (str)) -- message from the client.
    Returns:
        {"status": "ok"} 
    Prints: 
        Message that was saved.
        Example: "Saved message: Hello"
    """
    unique_id = query.UUID
    message = query.msg

    if msg_map.contains_key(unique_id):
        return {"status": "duplicate, ok"}
    
    msg_map.put(unique_id, message)
    print("Saved message: ", message)

    return {"status": "ok"} 


@app.get("/get_fetched_messages")
def get_fetched_messages() -> MessageResponseQuery:
    """
    Returns all messages from the Hash Table.

    Args:
        None
    Returns:
        {"msgs": "<all messages separated by ', '>"}
    """
    return {"msgs": ", ".join(msg_map.values())}
