"""Natural Language Processing utilities for MCP tools"""
import re
from typing import Optional, List, Dict, Tuple


# Priority keyword mappings
PRIORITY_KEYWORDS = {
    "high": ["urgent", "important", "critical", "asap", "emergency", "priority", "crucial"],
    "medium": ["normal", "regular", "moderate", "standard"],
    "low": ["low", "minor", "someday", "eventually", "later", "whenever"]
}

# Common tag patterns
TAG_PATTERNS = [
    r"with tags?\s+([a-zA-Z0-9,\s]+)",  # "with tag work" or "with tags work, urgent"
    r"tagged as\s+([a-zA-Z0-9,\s]+)",    # "tagged as work"
    r"tags:\s*([a-zA-Z0-9,\s]+)",        # "tags: work, personal"
    r"#(\w+)",                            # "#work #personal" (hashtag style)
]

# Filter intent patterns
PRIORITY_FILTER_PATTERNS = [
    (r"high priority", "high"),
    (r"urgent", "high"),
    (r"critical", "high"),
    (r"medium priority", "medium"),
    (r"normal priority", "medium"),
    (r"low priority", "low"),
]


def extract_priority_from_text(text: str) -> Optional[str]:
    """
    Extract priority level from natural language text.

    Args:
        text: Natural language text (e.g., "urgent meeting tomorrow")

    Returns:
        Priority level ("high", "medium", "low") or None if not found

    Examples:
        >>> extract_priority_from_text("urgent meeting tomorrow")
        "high"
        >>> extract_priority_from_text("maybe someday learn guitar")
        "low"
        >>> extract_priority_from_text("buy groceries")
        None
    """
    if not text:
        return None

    text_lower = text.lower()

    # Check each priority level's keywords
    for priority, keywords in PRIORITY_KEYWORDS.items():
        for keyword in keywords:
            # Match whole words only (avoid partial matches)
            if re.search(rf"\b{keyword}\b", text_lower):
                return priority

    return None


def extract_tags_from_text(text: str) -> List[str]:
    """
    Extract tags from natural language text using various patterns.

    Args:
        text: Natural language text

    Returns:
        List of extracted tags (lowercase, deduplicated)

    Examples:
        >>> extract_tags_from_text("meeting with tags work and urgent")
        ["work", "urgent"]
        >>> extract_tags_from_text("buy groceries #shopping #home")
        ["shopping", "home"]
        >>> extract_tags_from_text("call doctor tagged as health")
        ["health"]
    """
    if not text:
        return []

    tags = set()

    for pattern in TAG_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if pattern.startswith("#"):
                # Hashtag style - single tag per match
                tags.add(match.group(1).lower())
            else:
                # Phrase style - may contain multiple comma-separated tags
                tag_text = match.group(1)
                # Split by commas and "and"
                tag_list = re.split(r'[,\s]+and\s+|[,\s]+', tag_text)
                tags.update(tag.strip().lower() for tag in tag_list if tag.strip())

    return sorted(list(tags))


def parse_filter_intent(text: str) -> Dict[str, any]:
    """
    Parse filter intentions from natural language queries.

    Args:
        text: Natural language query (e.g., "show high priority work tasks")

    Returns:
        Dictionary with filter parameters: {priority, tags, search}

    Examples:
        >>> parse_filter_intent("show high priority tasks")
        {"priority": "high", "tags": [], "search": None}
        >>> parse_filter_intent("my work tasks")
        {"priority": None, "tags": ["work"], "search": None}
        >>> parse_filter_intent("find tasks about meeting")
        {"priority": None, "tags": [], "search": "meeting"}
    """
    filters = {
        "priority": None,
        "tags": [],
        "search": None
    }

    if not text:
        return filters

    text_lower = text.lower()

    # Extract priority filter
    for pattern, priority in PRIORITY_FILTER_PATTERNS:
        if re.search(pattern, text_lower):
            filters["priority"] = priority
            break

    # Extract tags (using same logic as extract_tags_from_text)
    filters["tags"] = extract_tags_from_text(text)

    # Extract search keywords
    # Look for "find", "search", "about", "containing" patterns
    search_patterns = [
        r"find (?:tasks? )?(?:about |containing |with )?['\"]?([^'\"]+?)['\"]?(?:\s|$)",
        r"search (?:for )?['\"]?([^'\"]+?)['\"]?(?:\s|$)",
        r"about ['\"]?([^'\"]+?)['\"]?(?:\s|$)",
        r"containing ['\"]?([^'\"]+?)['\"]?(?:\s|$)",
    ]

    for pattern in search_patterns:
        match = re.search(pattern, text_lower)
        if match:
            search_term = match.group(1).strip()
            # Remove common words that aren't useful for search
            stop_words = {"the", "a", "an", "tasks", "task", "my"}
            search_words = [w for w in search_term.split() if w not in stop_words]
            if search_words:
                filters["search"] = " ".join(search_words)
            break

    return filters


def normalize_priority(priority: Optional[str], text: Optional[str] = None) -> str:
    """
    Normalize priority value with fallback to NLP extraction.

    Args:
        priority: Explicit priority value (may be None)
        text: Text to extract priority from if explicit value not provided

    Returns:
        Normalized priority ("high", "medium", "low")

    Examples:
        >>> normalize_priority("HIGH")
        "high"
        >>> normalize_priority(None, "urgent meeting")
        "high"
        >>> normalize_priority(None, "buy groceries")
        "medium"
    """
    # If explicit priority provided, validate and normalize
    if priority:
        priority_lower = priority.lower()
        if priority_lower in ["high", "medium", "low"]:
            return priority_lower

    # Try NLP extraction from text
    if text:
        extracted_priority = extract_priority_from_text(text)
        if extracted_priority:
            return extracted_priority

    # Default to medium
    return "medium"


def normalize_tags(tags: Optional[List[str]], text: Optional[str] = None) -> List[str]:
    """
    Normalize tags with fallback to NLP extraction.

    Args:
        tags: Explicit tag list (may be None or empty)
        text: Text to extract tags from if explicit list not provided

    Returns:
        Normalized tag list (lowercase, deduplicated, sorted)

    Examples:
        >>> normalize_tags(["Work", "URGENT"], None)
        ["urgent", "work"]
        >>> normalize_tags(None, "meeting with tags work and urgent")
        ["urgent", "work"]
        >>> normalize_tags([], "call doctor #health")
        ["health"]
    """
    tag_set = set()

    # Add explicit tags if provided
    if tags:
        tag_set.update(tag.strip().lower() for tag in tags if tag.strip())

    # If no explicit tags, try NLP extraction
    if not tag_set and text:
        extracted_tags = extract_tags_from_text(text)
        tag_set.update(extracted_tags)

    return sorted(list(tag_set))


def extract_sort_intent(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract sorting preference from natural language.

    Args:
        text: Natural language query

    Returns:
        Tuple of (sort_by, sort_order) or (None, None)

    Examples:
        >>> extract_sort_intent("sort by priority")
        ("priority", None)
        >>> extract_sort_intent("show oldest first")
        ("created_at", "asc")
        >>> extract_sort_intent("newest tasks")
        ("created_at", "desc")
    """
    if not text:
        return None, None

    text_lower = text.lower()
    sort_by = None
    sort_order = None

    # Detect sort field
    if re.search(r"\bpriority\b", text_lower):
        sort_by = "priority"
    elif re.search(r"\btitle\b|\bname\b|\balphabet", text_lower):
        sort_by = "title"
    elif re.search(r"\bdate\b|\btime\b|\bcreated\b|\bnew", text_lower):
        sort_by = "created_at"

    # Detect sort order
    if re.search(r"\boldest\b|\bfirst\b|\bearliest\b|\bascending\b|\basc\b", text_lower):
        sort_order = "asc"
    elif re.search(r"\bnewest\b|\blast\b|\blatest\b|\brecent\b|\bdescending\b|\bdesc\b", text_lower):
        sort_order = "desc"

    return sort_by, sort_order
