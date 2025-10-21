# Werken: An Asynchronous Workflow Engine

Werken is a lightweight, event-driven workflow engine built with Python, FastAPI, and RabbitMQ. It's designed to receive webhooks, process them according to predefined workflows, and dispatch actions to be executed by other services.

## Architecture

The architecture is simple and scalable. It consists of the following components:

```
+----------+      +-----------------+      +---------------------+      +-------------------+
| Webhook  |----->| Ingestor (API)  |----->| RabbitMQ            |----->| Workflow Engine   |
| (POST)   |      | (FastAPI)       |      | (received_webhooks) |      | (Python)          |
+----------+      +-----------------+      +---------------------+      +-------------------+
                                                                              |
                                                                              v
                                                                    +---------------------+
                                                                    | RabbitMQ            |
                                                                    | (required_actions)  |
                                                                    +---------------------+
                                                                              |
                                                                              v
                                                                    +-------------------+
                                                                    | Workers (Email,   |
                                                                    | Logging, etc.)    |
                                                                    +-------------------+
```

1.  **Ingestor**: A FastAPI application that exposes a `/webhook/{workflow_id}` endpoint to receive incoming webhooks. It validates the request and publishes the webhook data to the `received_webhooks` queue in RabbitMQ.
2.  **RabbitMQ**: The message broker that decouples the ingestor from the workflow engine. It uses two main queues:
    *   `received_webhooks`: For incoming webhooks.
    *   `required_actions`: For actions that need to be executed.
3.  **Workflow Engine**: A Python script that consumes messages from the `received_webhooks` queue. It reads the `workflows.json` file to determine the actions to be executed for a given `workflow_id` and publishes them to the `required_actions` queue.
4.  **Workers**: (Not included in this project) These are separate services that would consume messages from the `required_actions` queue and perform the actual work (e.g., sending emails, processing images, etc.).

## Getting Started

### Prerequisites

*   Docker
*   Docker Compose

### Installation

1.  Clone the repository:
    ```sh
    git clone <your-repo-url>
    cd werken
    ```
2.  Start the services using Docker Compose:
    ```sh
    docker-compose up --build -d
    ```
    This will start the `rabbitmq`, `ingestor`, and `workflow-engine` services.

## Usage

To trigger a workflow, send a `POST` request to the `ingestor` service. You need to specify the `workflow_id` in the URL.

For example, to trigger the `mi-workflow` defined in `workflow-engine/workflows.json`, you can use `curl`:

```sh
curl -X POST http://localhost:8000/webhook/mi-workflow \
-H "Content-Type: application/json" \
-d 
'{ 
  "user_id": 123,
  "data": "some important data"
}'
```

curl -X POST -H "Content-Type: application/json" -d '{"user": "adrian", "actions": "enviar_notificacion"}' http://localhost:8000/webhook/blog-nuevo-post

This will publish a message to the `received_webhooks` queue. The `workflow-engine` will then process it and publish the corresponding actions to the `required_actions` queue.

## Testing

To run the integration tests, you need to have the services running.

1.  Install the test dependencies:
    ```sh
    pip install -r tests/requirements.txt
    ```
2.  Run the test script:
    ```sh
    python tests/test_integration.py
    ```

## Configuration

Workflows are defined in the `workflow-engine/workflows.json` file. You can add new workflows or modify existing ones. Each workflow has a unique ID and a list of actions.

Here is an example of a workflow definition:

```json
{
  "mi-workflow": {
    "description": "Workflow de prueba para mi blog",
    "actions": [
      {
        "type": "enviar_email",
        "params": {
          "destinatario": "gaby@example.com",
          "asunto": "¡Webhook Recibido con Éxito!",
          "cuerpo": "Se ha recibido y procesado un webhook para 'mi-workflow'."
        }
      },
      {
        "type": "log_evento",
        "params": {
          "nivel": "info",
          "mensaje": "El workflow de mi-blog se ha ejecutado."
        }
      }
    ]
  }
}
```

## Project Structure

```
.
├── docker-compose.yml
├── ingestor
│   ├── Dockerfile
│   ├── main.py
│   └── requeriments.txt
└── workflow-engine
    ├── Dockerfile
    ├── engine.py
    ├── requeriments.txt
    └── workflows.json
```

*   `ingestor`: Contains the FastAPI application for receiving webhooks.
*   `workflow-engine`: Contains the core logic for processing workflows.

```