import requests
import pika
import json
import time

def test_workflow():
    # Send a webhook to the ingestor
    workflow_id = "user-registered"
    payload = {"user_id": 123, "data": "some important data"}
    response = requests.post(f"http://localhost:8000/webhook/{workflow_id}", json=payload)
    assert response.status_code == 200

    # Connect to RabbitMQ and check the required_actions queue
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Wait for the workflow engine to process the message
    time.sleep(5)  # Adjust this based on your system's performance

    # Get the messages from the required_actions queue
    messages = []
    for method_frame, properties, body in channel.consume('required_actions', inactivity_timeout=1):
        if body is None:
            break
        messages.append(json.loads(body))
        channel.basic_ack(method_frame.delivery_tag)

    # Assert that the correct actions were published
    assert len(messages) == 2

    # Check the first action
    assert messages[0]['action_type'] == 'send_notification'
    assert messages[0]['action_params']['channel'] == 'email'

    # Check the second action
    assert messages[1]['action_type'] == 'archive_event'
    assert messages[1]['action_params']['event'] == 'registration'

    print("✅ Integration test passed!")

if __name__ == "__main__":
    test_workflow()
