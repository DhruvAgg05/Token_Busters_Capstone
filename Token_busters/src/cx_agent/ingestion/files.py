from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from cx_agent.models import Customer, Event


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def save_customers(path: Path, customers: Iterable[Customer]) -> None:
    write_json(path, [customer.__dict__ for customer in customers])


def save_events(path: Path, events: Iterable[Event]) -> None:
    write_json(path, [event.__dict__ for event in events])


def save_events_by_source(directory: Path, events: Iterable[Event]) -> None:
    grouped_events: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        grouped_events[source_bucket_for_channel(event.channel)].append(event)

    directory.mkdir(parents=True, exist_ok=True)
    for source_name in sorted(grouped_events):
        source_events = sorted(grouped_events[source_name], key=lambda event: event.timestamp_value())
        write_json(directory / f"{source_name}.json", [event.__dict__ for event in source_events])


def load_customers(path: Path) -> list[Customer]:
    payload = read_json(path)
    return [Customer(**item) for item in payload]


def load_events(path: Path) -> list[Event]:
    payload = read_json(path)
    return [Event(**item) for item in payload]


def load_events_from_source_directory(directory: Path) -> list[Event]:
    if not directory.exists():
        return []

    events: list[Event] = []
    for path in sorted(directory.glob("*.json")):
        payload = read_json(path)
        if isinstance(payload, list):
            events.extend(Event(**item) for item in payload)
    return events


def source_bucket_for_channel(channel: str) -> str:
    normalized = channel.lower()
    if normalized in {"payment", "transaction"}:
        return "payments"
    if normalized in {"email", "communication"}:
        return "communications"
    if normalized == "survey":
        return "surveys"
    return normalized
