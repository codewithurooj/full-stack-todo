# Event Replay Scripts

**Feature 011: Event-Driven Architecture with Kafka**

Administrative scripts for Kafka event management, replay, and recovery.

## Installation

```bash
cd services/scripts
pip install -r requirements.txt
```

## Available Scripts

### replay_events.py

CLI tool for replaying events from Kafka topics for disaster recovery, testing, and debugging.

**Usage:**

```bash
# Replay all events from beginning
python replay_events.py --topic task-events --from-beginning

# Replay from specific timestamp
python replay_events.py --topic task-events --from-time "2026-01-13 12:00:00"

# Replay from specific offset
python replay_events.py --topic task-events --offset 1000 --partition 0

# Dry run (don't commit offsets)
python replay_events.py --topic task-events --from-beginning --dry-run

# Replay limited number of events
python replay_events.py --topic task-events --from-beginning --max-events 100

# Custom Kafka bootstrap servers
python replay_events.py --topic task-events --from-beginning --bootstrap-servers kafka:9092
```

**Arguments:**

- `--topic` (required): Kafka topic to replay
- `--from-beginning`: Replay from beginning of topic
- `--from-time`: Replay from specific timestamp (format: YYYY-MM-DD HH:MM:SS)
- `--offset`: Replay from specific offset (requires --partition)
- `--partition`: Partition number (required with --offset)
- `--bootstrap-servers`: Kafka bootstrap servers (default: localhost:19092)
- `--consumer-group`: Consumer group ID (default: replay-group)
- `--max-events`: Maximum number of events to replay
- `--dry-run`: Don't commit offsets (read-only mode)
- `--debug`: Enable debug logging

**See:** docs/runbooks/event-replay.md for detailed procedures
