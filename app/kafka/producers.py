from aiokafka import AIOKafkaProducer
import sys, asyncio, json
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
sys.path.append(app_dir)

from app.config import settings
from app.logger import logger


class KafkaProducerManager:
    def __init__(self, loop, bootstrap_servers):
        self.loop = loop
        self.bootstrap_servers = bootstrap_servers
        self.producers = {}

    async def send(self, topic: str, value: dict):
        producer = AIOKafkaProducer(
            loop=self.loop,
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        # get cluster layout and initial topic/partition leadership information
        await producer.start()
        try:
            # produce message
            logger.info(f'Sending message with value: {value}')
            await producer.send_and_wait(topic, value)
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"failed to send message with value: {value}")
        finally:
            # wait for all pending messages to be delivered or expire.
            await producer.stop()

loop = asyncio.get_event_loop()

producer_manager = KafkaProducerManager(
    loop=loop, 
    bootstrap_servers=settings.bootstrap_servers
)