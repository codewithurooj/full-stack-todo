"""
Checkpoint and Offset Tracking
Provides manual checkpoint management for testing and recovery scenarios
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages consumer offset checkpoints for recovery testing

    Note: In production, Kafka consumer groups automatically track offsets.
    This module is for testing and manual recovery scenarios.
    """

    def __init__(self, checkpoint_file: str = "checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.offsets: Dict[int, int] = {}

    def save_checkpoint(self, partition: int, offset: int):
        """
        Save checkpoint for a partition

        Args:
            partition: Partition number
            offset: Offset to checkpoint
        """
        self.offsets[partition] = offset

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(self.offsets, f, indent=2)

            logger.info(f"Checkpoint saved: partition={partition}, offset={offset}")

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def load_checkpoint(self) -> Dict[int, int]:
        """
        Load checkpoints from file

        Returns:
            Dictionary of partition -> offset mappings
        """
        if not self.checkpoint_file.exists():
            logger.info("No checkpoint file found")
            return {}

        try:
            with open(self.checkpoint_file, 'r') as f:
                self.offsets = json.load(f)

            # Convert string keys to integers
            self.offsets = {int(k): v for k, v in self.offsets.items()}

            logger.info(f"Checkpoint loaded: {self.offsets}")
            return self.offsets

        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return {}

    def get_offset(self, partition: int) -> Optional[int]:
        """
        Get checkpoint offset for partition

        Args:
            partition: Partition number

        Returns:
            Offset or None if not found
        """
        return self.offsets.get(partition)

    def clear_checkpoint(self):
        """Clear all checkpoints"""
        self.offsets = {}

        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            logger.info("Checkpoint cleared")

    def get_all_offsets(self) -> Dict[int, int]:
        """Get all partition offsets"""
        return self.offsets.copy()
