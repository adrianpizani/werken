import json
import pika
import time
import sys

try:
    with open("workflows.json",'r') as f:
        WORKFLOWS = json.load(f)
    print("✅ Workflows loaded!")
except FileNotFoundError:
    print("❌ Error: 'workflows.json' noot found.")
    sys.exit(1)

MAX_RETRIES = 15
RETRY_DELAY = 3

for i in range(MAX_RETRIES):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=600))
        channel = connection.channel()
        channel.queue_declare('received_webhooks', durable=True)
        channel.queue_declare('required_actions', durable=True)
        print("✅ RabbitMQ connection stablished.")
        break
    except Exception as e:
        print(f"Engine error connecting to RabbitMQ: {e}. Retrying...")
        time.sleep(RETRY_DELAY)
else:
    print("❌ Can't connect Engine to RabbitMQ. Closing  application")
    sys.exit(1)


def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        workflow_id = message.get('workflow_id')
        payload = message.get('payload')
        print(f"▶️ Engine: Processing webhook for '{workflow_id}'...")

        if workflow_id in WORKFLOWS:
            for action in WORKFLOWS[workflow_id]['actions']:
                new_message = {
                    'action_type': action['type'],
                    'action_params': action['params'],
                    'original_payload': payload,
                }
                channel.basic_publish(
                    exchange='',
                    routing_key='required_actions',
                    body=json.dumps(new_message).encode('utf-8'),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                print(f"  ↪️ Engine: Action published '{action['type']}' for '{workflow_id}'.")
        else:
            print(f"⚠️ Engine: {workflow_id} not found in config.")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"❌ Engine: Error processing message: {e}")


# Consumption
channel.basic_consume('received_webhooks', on_message_callback=callback)
print('[*] The workflow is waiting for messages. To quit, press CTRL+C')
channel.start_consuming()




