"""Analysis history tracking for kagent.

Maintains history of cluster health analyses.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class AnalysisHistory:
    """Tracks history of cluster analyses."""

    def __init__(self, tool_name: str):
        """Initialize history tracker.

        Args:
            tool_name: Name of the tool (kagent)
        """
        self.tool_name = tool_name
        self.history_dir = Path.home() / f".{tool_name}" / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        self.history_file = self.history_dir / "analysis_history.jsonl"

    def save(self, analysis: Dict[str, Any]) -> None:
        """Save analysis to history.

        Args:
            analysis: Analysis data to save
        """
        # Ensure timestamp
        if 'timestamp' not in analysis:
            analysis['timestamp'] = datetime.utcnow().isoformat()

        # Append to history file
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(analysis) + '\n')

        logger.info(f"Analysis saved to history: {analysis['timestamp']}")

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Get latest analysis.

        Returns:
            Latest analysis data or None
        """
        analyses = self.get_all(limit=1)
        return analyses[0] if analyses else None

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all analyses.

        Args:
            limit: Maximum number of analyses to return

        Returns:
            List of analysis data
        """
        if not self.history_file.exists():
            return []

        analyses = []

        with open(self.history_file, 'r') as f:
            for line in f:
                try:
                    analysis = json.loads(line)
                    analyses.append(analysis)
                except json.JSONDecodeError:
                    continue

        # Return most recent first
        return analyses[-limit:][::-1]

    def get_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get analyses for a specific date.

        Args:
            date_str: Date string (YYYY-MM-DD)

        Returns:
            List of analyses for that date
        """
        all_analyses = self.get_all(limit=1000)

        filtered = [
            a for a in all_analyses
            if a.get('timestamp', '').startswith(date_str)
        ]

        return filtered

    def get_trend(self, days: int = 7) -> Dict[str, List[int]]:
        """Get trend data for last N days.

        Args:
            days: Number of days to analyze

        Returns:
            Trend data with counts by severity
        """
        all_analyses = self.get_all(limit=days * 10)  # Assume max 10 analyses per day

        trend = {
            'dates': [],
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'total': []
        }

        # Group by date
        by_date = {}
        for analysis in all_analyses:
            timestamp = analysis.get('timestamp', '')
            date = timestamp.split('T')[0] if timestamp else 'unknown'

            if date not in by_date:
                by_date[date] = []
            by_date[date].append(analysis)

        # Calculate averages per date
        for date in sorted(by_date.keys())[-days:]:
            analyses = by_date[date]

            avg_critical = sum(a.get('critical', 0) for a in analyses) // len(analyses)
            avg_high = sum(a.get('high', 0) for a in analyses) // len(analyses)
            avg_medium = sum(a.get('medium', 0) for a in analyses) // len(analyses)
            avg_low = sum(a.get('low', 0) for a in analyses) // len(analyses)
            avg_total = sum(a.get('findings_count', 0) for a in analyses) // len(analyses)

            trend['dates'].append(date)
            trend['critical'].append(avg_critical)
            trend['high'].append(avg_high)
            trend['medium'].append(avg_medium)
            trend['low'].append(avg_low)
            trend['total'].append(avg_total)

        return trend

    def clear_old(self, days: int = 30) -> int:
        """Clear analyses older than N days.

        Args:
            days: Number of days to retain

        Returns:
            Number of entries removed
        """
        if not self.history_file.exists():
            return 0

        cutoff = datetime.now().timestamp() - (days * 24 * 3600)
        kept = []
        removed = 0

        with open(self.history_file, 'r') as f:
            for line in f:
                try:
                    analysis = json.loads(line)
                    timestamp_str = analysis.get('timestamp', '')

                    if timestamp_str:
                        analysis_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if analysis_time.timestamp() >= cutoff:
                            kept.append(line)
                        else:
                            removed += 1
                except (json.JSONDecodeError, ValueError):
                    continue

        # Rewrite file with kept entries
        with open(self.history_file, 'w') as f:
            f.writelines(kept)

        logger.info(f"Removed {removed} old analysis entries")
        return removed
