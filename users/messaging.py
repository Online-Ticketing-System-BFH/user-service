import json
import logging
import asyncio
import aio_pika
from aio_pika import ExchangeType
from django.conf import settings
from .tasks import send_booking_confirmation_email_task

logger = logging.getLogger(__name__)

async def on_reservation_confirmed(message):
    """Handler for reservation.confirmed event."""
    try:
        body = json.loads(message.body.decode())
        data = body.get("data", {})
        user_id_str = data.get("user_id")
        
        if not user_id_str:
            logger.warning("Received reservation.confirmed without user_id")
            return

        # The user_id is a UUID(int=auth_id) stringified
        # We need to extract the numeric auth_id
        import uuid
        try:
            u = uuid.UUID(user_id_str)
            auth_id = u.int
        except ValueError:
            logger.error(f"Invalid user_id format in event: {user_id_str}")
            return

        logger.info(f"Processing booking confirmation for auth_id: {auth_id}")
        
        # Trigger Celery task to send email
        send_booking_confirmation_email_task.delay(auth_id, data)
        
    except Exception as e:
        logger.error(f"Error in on_reservation_confirmed: {e}", exc_info=True)

async def start_consumer():
    """Start RabbitMQ consumer."""
    rabbitmq_url = getattr(settings, "CELERY_BROKER_URL", "redis://redis:6379/0")
    # If CELERY_BROKER_URL is redis, we might need a separate RABBITMQ_URL
    # Let's check settings or use default
    rabbitmq_url = "amqp://guest:guest@rabbitmq:5672/"
    exchange_name = "ticketing_events"
    queue_name = "user_service_notifications"

    logger.info(f"Connecting to RabbitMQ at {rabbitmq_url}")
    
    # Add a simple retry loop for initial connection
    connection = None
    for i in range(10):
        try:
            connection = await aio_pika.connect_robust(rabbitmq_url)
            break
        except Exception as e:
            logger.warning(f"Connection attempt {i+1} failed: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
    
    if not connection:
        logger.error("Failed to connect to RabbitMQ after multiple attempts.")
        return
    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)

        exchange = await channel.declare_exchange(
            exchange_name,
            ExchangeType.TOPIC,
            durable=True
        )

        queue = await channel.declare_queue(
            queue_name,
            durable=True
        )

        # Bind to the reservation.confirmed event
        await queue.bind(exchange, routing_key="reservation.confirmed")

        logger.info(f"Started consuming from {queue_name}")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await on_reservation_confirmed(message)
