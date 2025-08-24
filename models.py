from dataclasses import dataclass
from typing import Tuple


@dataclass
class Actor:
    """Represents an entity interacting with the editor."""
    name: str
    actor_type: str
    color: Tuple[int, int, int]


class ActorFactory:
    """Factory for creating typed actors with default colors."""

    TYPE_COLORS = {
        "Business": (0, 102, 204),      # blue
        "Government": (0, 153, 0),      # green
        "Gym": (204, 102, 0),           # orange
    }

    @classmethod
    def create(cls, name: str, actor_type: str) -> Actor:
        color = cls.TYPE_COLORS.get(actor_type, (255, 0, 0))
        return Actor(name=name, actor_type=actor_type, color=color)


@dataclass
class Shape:
    """A drawn shape bound to an actor."""
    typ: str
    data: tuple
    actor: Actor
