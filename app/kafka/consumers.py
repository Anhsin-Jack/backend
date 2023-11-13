import aiokafka, sys, json, asyncio
from kafka import TopicPartition
from typing import Set

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(app_dir)
from . import config, actions
from ..logger import logger
from ..config import settings


class KafkaConsumeManager:
    def __init__(self, loop, bootstrap_servers):
        self.loop = loop
        self.bootstrap_servers = bootstrap_servers
        self.consumers = {}

    async def create_bg_consumer(self, topic: str, group_id: str = "default"):
        try:
            logger.debug(
                'Initializing KafkaConsumer '
                f'for topic {topic}, group_id {group_id} '
                f'and using bootstrap servers {self.bootstrap_servers}'
            )
            consumer = aiokafka.AIOKafkaConsumer(
                topic, 
                loop=self.loop,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id
            )
            
            self.consumers[topic] = consumer
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"Error creating Kafka consumer for topic '{topic}'")

    async def start_bg_consumer(self, topic):
        try:
            # Get cluster layout and join group
            await self.consumers.get(topic).start()

            partitions: Set[TopicPartition] = self.consumers.get(topic).assignment()

            nr_partitions = len(partitions)
            if nr_partitions != 1:
                pass
                logger.warning(
                    f"Found {nr_partitions} partitions "
                    f"for topic {topic}. Expecting "
                    "only one, remaining partitions will be ignored!"
                )
            for tp in partitions:
                # Get the log_end_offset
                end_offset_dict = await self.consumers.get(topic).end_offsets([tp])
                end_offset = end_offset_dict[tp]

                if end_offset == 0:
                    logger.warning(
                        f'Topic ({topic}) has no messages (log_end_offset: '
                        f'{end_offset}), skipping initialization ...'
                    )
                    return None

                logger.debug(
                    'Found log_end_offset: '
                    f'{end_offset} seeking to {end_offset-1}'
                )
                self.consumers.get(topic).seek(tp, end_offset-1)
                msg = await self.consumers.get(topic).getone()
                logger.info(f'Initializing API with data from msg: {msg}')
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"Error starting Kafka consumer for topic '{topic}'")

    async def bg_consume(self, topic):
        await self.start_bg_consumer(topic)
        consumer = self.consumers.get(topic)
        try:
            if consumer:
                 # Consume messages
                async for msg in consumer:
                    action = json.loads(msg.value).get("action")
                    data = json.loads(msg.value).get("data")
                    logger.info(f"Consumed BG msg: {msg}")

                    match action:
                        case config.KafkaAction.SAVE_REQUEST_TO_DB:
                            await actions.save_request_to_db(data)
                        case config.KafkaAction.SAVE_RESPONSE_TO_DB:
                            await actions.save_response_to_db(data)
                        case config.KafkaAction.WRITE_DB:
                            schemas = data.get("schemas")
                            data.pop("schemas")
                            await actions.write_db(data, schemas)
                        case config.KafkaAction.UPDATE_DB:
                            schemas = data.get("schemas")
                            data.pop("schemas")
                            update_data = data.get("update_data")
                            data.pop("update_data")
                            filters = data.get("filters")
                            data.pop("filters")
                            await actions.update_db(
                                schemas, update_data, filters
                            )
                        case _:
                            logger.error(
                                f'Does not support action "{e}"', 
                                exc_info=sys.exc_info()
                            )
                            raise KeyError(
                                f'Does not support action "{e}"'
                            )
            else:
                raise KeyError(f"Consumer for topic '{topic}' not found")
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(
                f"Error while consuming messages for topic '{topic}'"
            )
        finally:
            # Leave consumer group; perform autocommit if enabled
            logger.warning('Stopping consumer')
            try:
                await self.stop_consumer(topic)
            except Exception as e:
                logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
                raise KeyError(
                    f"Error while stopping Kafka consumer for topic '{topic}'"
                )

    async def create_ot_consumer(self, topic: str, group_id: str = "default"):
        try:
            logger.debug(
                'Initializing KafkaConsumer '
                f'for topic {topic}, group_id {group_id} '
                f'and using bootstrap servers {self.bootstrap_servers}'
            )

            consumer = aiokafka.AIOKafkaConsumer(
                topic,
                loop=self.loop,
                bootstrap_servers=self.bootstrap_servers,
                group_id=group_id,  # unique identifier for each sidecar
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,  # commit every second
                auto_offset_reset="earliest",  # If committed offset not found, start from beginning
                max_poll_records=1
            )
            
            self.consumers[topic] = consumer
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"Error creating Kafka consumer for topic '{topic}'")
        
    async def start_ot_consumer(self, topic):
        try:
            # Get cluster layout and join group
            await self.consumers.get(topic).start()
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"Error starting Kafka consumer for topic '{topic}'")

    async def ot_consume(self, topic):
        consumer = self.consumers.get(topic)
        try:
            msg = await consumer.getone()
            if msg:
                action = json.loads(msg.value).get("action")
                data = json.loads(msg.value).get("data")
                logger.info(f"Consumed OT msg: {msg}")

                match action:
                    case config.KafkaAction.DELETE_DB:
                        schemas = data.get("schemas")
                        filters = data.get("filters")
                        result = await actions.delete_db(
                            schemas=schemas, 
                            filters=filters
                        )
                    case config.KafkaAction.READ_DB:
                        schemas = data.get("schemas", None)
                        operation = data.get("operation", None)
                        columns = data.get("columns", None)
                        filters = data.get("filters", None)
                        result = await actions.read_db(
                            schemas=schemas, 
                            operation=operation, 
                            columns=columns, 
                            filters=filters
                        )
                    case _:
                        logger.error(
                            f'Does not support action "{e}"', 
                            exc_info=sys.exc_info()
                        )
                        raise KeyError(
                            f'Does not support action "{e}"'
                        )
            else:
                raise KeyError(f"Consumer for topic '{topic}' not found")
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(
                f"Error while consuming messages for topic '{topic}'"
            )
        return result
    
    async def stop_consumer(self, topic):
        try:
            await self.consumers.get(topic).stop()
        except Exception as e:
            logger.error(f'An error occurred: {e}', exc_info=sys.exc_info())
            raise KeyError(f"Error stopping Kafka consumer for topic '{topic}'")

loop = asyncio.get_event_loop()

consumer_manager = KafkaConsumeManager(
    loop=loop, 
    bootstrap_servers=settings.bootstrap_servers
)