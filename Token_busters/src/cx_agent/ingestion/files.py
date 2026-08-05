from __future__ import annotations

import json
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


def load_customers(path: Path) -> list[Customer]:
    payload = read_json(path)
    return [Customer(**item) for item in payload]


def load_events(path: Path) -> list[Event]:
    payload = read_json(path)
    return [Event(**item) for item in payload]

