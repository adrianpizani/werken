import pika
import json
from fastapi import FastAPI, Request, HTTPException
import pika.exceptions
import time
import sys

app = FastAPI()

MAX_RETRIES = 15
RETRY_DELAY = 3
connection = None
channel = None

for i in range(MAX_RETRIES):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq')) # Docker will solve it
        channel = connection.channel()
        channel.queue_declare(queue='received_webhooks', durable=True) #queue will persist after rabbit restart
        print("✅ Conexión con RabbitMQ establecida exitosamente.")
        break
    except pika.exceptions.AMQPConnectionError as e:
        print(f"Error conectandose a la cola RabbitMQ: {e}. Reintentando en {RETRY_DELAY}")
        time.sleep(RETRY_DELAY)
else:
    print("❌ No se pudo establecer conexión con RabbitMQ después de varios intentos. Saliendo.")
    sys.exit(1)

@app.post("/webhook/{workflow_id}")
async def receive_webhook(workflow_id: str, request: Request):

    print(f"webhook received with the workflow_id: {workflow_id}")
    try:
        webhook_data = await request.json()
        message = {
            'workflow_id': workflow_id,
            'payload': webhook_data
        }
        # Convert dict message to string JSON and encode to bytes, then publish to Pika
        channel.basic_publish(
            exchange='',
            routing_key='received_webhooks',
            body=json.dumps(message).encode('utf-8'),
            # Make message persistant 
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )
        print(f"Message for {workflow_id} published in the received_webhooks queue.")
        return {"status": 'ok', "message": "message delivered to the queue"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Petition body request not JSON valid")
    
    except Exception as e:
        print(f"Error processing the webhoook {e}")
        raise HTTPException(status_code=400, detail="Internal error")









