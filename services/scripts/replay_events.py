#!/usr/bin/env python3
"""
Event Replay CLI Tool
Feature 011: Event-Driven Architecture with Kafka

Replays events from Kafka topics for disaster recovery, testing, and debugging.

Usage:
    # Replay from specific offset
    python replay_events.py --topic task-events --offset 1000 --consumer-group replay-group

    # Replay from timestamp
    python replay_events.py --topic task-events --from-time "2026-01-13 12:00:00" --consumer-group replay-group

    # Replay all events from beginning
    python replay_events.py --topic task-events --from-beginning --consumer-group replay-group

    # Dry run (don't commit offsets)
    python replay_events.py --topic task-events --from-beginning --dry-run
"""
import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Optional
from kafka import KafkaConsumer, TopicPartition, OffsetAndTimestamp
from kafka.errors import KafkaError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventReplayer:
    """Replays events from Kafka topics"""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        consumer_group: str,
        dry_run: bool = False
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer_group = consumer_group
        self.dry_run = dry_run
        self.consumer = None
        self.events_replayed = 0

    def connect(self):
        """Connect to Kafka and create consumer"""
        logger.info(f"Connecting to Kafka: {self.bootstrap_servers}")
        logger.info(f"Topic: {self.topic}")
        logger.info(f"Consumer Group: {self.consumer_group}")
        logger.info(f"Dry Run: {self.dry_run}")

        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=not self.dry_run,  # Disable auto-commit in dry-run
                max_poll_interval_ms=300000,  # 5 minutes
                session_timeout_ms=60000,  # 1 minute
            )

            logger.info("Connected to Kafka successfully")
            return True

        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            return False

    def seek_to_offset(self, partition: int, offset: int):
        """Seek to specific offset in partition"""
        tp = TopicPartition(self.topic, partition)
        self.consumer.assign([tp])
        self.consumer.seek(tp, offset)
        logger.info(f"Seeking to partition {partition}, offset {offset}")

    def seek_to_timestamp(self, timestamp: datetime):
        """Seek to specific timestamp"""
        timestamp_ms = int(timestamp.timestamp() * 1000)
        logger.info(f"Seeking to timestamp: {timestamp} ({timestamp_ms}ms)")

        # Get all partitions for the topic
        partitions = self.consumer.partitions_for_topic(self.topic)
        if not partitions:
            logger.error(f"No partitions found for topic: {self.topic}")
            return False

        # Create TopicPartition objects for all partitions
        topic_partitions = {
            TopicPartition(self.topic, p): timestamp_ms
            for p in partitions
        }

        # Assign all partitions
        self.consumer.assign(list(topic_partitions.keys()))

        # Seek to timestamp
        offsets_for_times = self.consumer.offsets_for_times(topic_partitions)

        for tp, offset_and_timestamp in offsets_for_times.items():
            if offset_and_timestamp is not None:
                self.consumer.seek(tp, offset_and_timestamp.offset)
                logger.info(
                    f"Partition {tp.partition}: seeking to offset {offset_and_timestamp.offset}"
                )
            else:
                logger.warning(
                    f"Partition {tp.partition}: no offset found for timestamp, "
                    f"seeking to end"
                )
                self.consumer.seek_to_end(tp)

        return True

    def seek_to_beginning(self):
        """Seek to beginning of all partitions"""
        logger.info("Seeking to beginning of topic")

        # Get all partitions
        partitions = self.consumer.partitions_for_topic(self.topic)
        if not partitions:
            logger.error(f"No partitions found for topic: {self.topic}")
            return False

        # Assign and seek to beginning
        topic_partitions = [TopicPartition(self.topic, p) for p in partitions]
        self.consumer.assign(topic_partitions)
        self.consumer.seek_to_beginning(*topic_partitions)

        logger.info(f"Subscribed to {len(topic_partitions)} partitions")
        return True

    def replay_events(self, max_events: Optional[int] = None):
        """Replay events from current position"""
        logger.info("Starting event replay...")

        if max_events:
            logger.info(f"Max events to replay: {max_events}")
        else:
            logger.info("Replaying all events until end of topic")

        try:
            while True:
                # Poll for messages
                messages = self.consumer.poll(timeout_ms=1000, max_records=100)

                if not messages:
                    logger.info("No more messages available")
                    break

                for tp, records in messages.items():
                    for record in records:
                        self.events_replayed += 1

                        # Log event details
                        event = record.value
                        event_type = event.get('event_type', 'unknown')
                        event_id = event.get('event_id', 'unknown')

                        logger.info(
                            f"[{self.events_replayed}] "
                            f"Partition={tp.partition}, "
                            f"Offset={record.offset}, "
                            f"Type={event_type}, "
                            f"ID={event_id}"
                        )

                        # Log full event in debug mode
                        logger.debug(f"Event payload: {json.dumps(event, indent=2)}")

                        # Check max events limit
                        if max_events and self.events_replayed >= max_events:
                            logger.info(f"Reached max events limit: {max_events}")
                            return

                # Commit offsets if not dry-run
                if not self.dry_run:
                    self.consumer.commit()
                    logger.debug("Committed offsets")

        except KeyboardInterrupt:
            logger.info("Replay interrupted by user")

        except Exception as e:
            logger.error(f"Error during replay: {e}", exc_info=True)
            raise

        finally:
            logger.info(f"Replay complete: {self.events_replayed} events replayed")

    def close(self):
        """Close consumer connection"""
        if self.consumer:
            self.consumer.close()
            logger.info("Consumer closed")


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp string to datetime"""
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Could not parse timestamp: {timestamp_str}. "
        f"Use format: YYYY-MM-DD HH:MM:SS"
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Replay events from Kafka topics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replay from specific offset
  python replay_events.py --topic task-events --offset 1000 --partition 0

  # Replay from timestamp
  python replay_events.py --topic task-events --from-time "2026-01-13 12:00:00"

  # Replay all events from beginning
  python replay_events.py --topic task-events --from-beginning

  # Dry run (don't commit offsets)
  python replay_events.py --topic task-events --from-beginning --dry-run

  # Replay limited number of events
  python replay_events.py --topic task-events --from-beginning --max-events 100
        """
    )

    # Required arguments
    parser.add_argument(
        '--bootstrap-servers',
        default='localhost:19092',
        help='Kafka bootstrap servers (default: localhost:19092)'
    )
    parser.add_argument(
        '--topic',
        required=True,
        help='Kafka topic to replay'
    )
    parser.add_argument(
        '--consumer-group',
        default='replay-group',
        help='Consumer group ID (default: replay-group)'
    )

    # Seek mode (mutually exclusive)
    seek_group = parser.add_mutually_exclusive_group(required=True)
    seek_group.add_argument(
        '--from-beginning',
        action='store_true',
        help='Replay from beginning of topic'
    )
    seek_group.add_argument(
        '--from-time',
        type=str,
        help='Replay from specific timestamp (YYYY-MM-DD HH:MM:SS)'
    )
    seek_group.add_argument(
        '--offset',
        type=int,
        help='Replay from specific offset (requires --partition)'
    )

    # Optional arguments
    parser.add_argument(
        '--partition',
        type=int,
        help='Partition number (required with --offset)'
    )
    parser.add_argument(
        '--max-events',
        type=int,
        help='Maximum number of events to replay'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't commit offsets (read-only mode)"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate arguments
    if args.offset is not None and args.partition is None:
        parser.error("--offset requires --partition")

    # Create replayer
    replayer = EventReplayer(
        bootstrap_servers=args.bootstrap_servers,
        topic=args.topic,
        consumer_group=args.consumer_group,
        dry_run=args.dry_run
    )

    try:
        # Connect to Kafka
        if not replayer.connect():
            logger.error("Failed to connect to Kafka")
            return 1

        # Seek to desired position
        if args.from_beginning:
            if not replayer.seek_to_beginning():
                return 1

        elif args.from_time:
            try:
                timestamp = parse_timestamp(args.from_time)
                if not replayer.seek_to_timestamp(timestamp):
                    return 1
            except ValueError as e:
                logger.error(str(e))
                return 1

        elif args.offset is not None:
            replayer.seek_to_offset(args.partition, args.offset)

        # Replay events
        replayer.replay_events(max_events=args.max_events)

        logger.info("Event replay completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.info("Replay interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Replay failed: {e}", exc_info=True)
        return 1

    finally:
        replayer.close()


if __name__ == '__main__':
    sys.exit(main())
