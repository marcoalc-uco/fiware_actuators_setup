from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class EntityRef(BaseModel):
    """Entity reference for subscription subject.

    Parameters
    ----------
    idPattern : str
        Regex pattern for entity IDs.
    type : str
        Entity type.
    """

    idPattern: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)


class Subject(BaseModel):
    """Subscription subject definition.

    Parameters
    ----------
    entities : List[EntityRef]
        List of entities to subscribe to.
    condition : dict[str, Any], optional
        Condition to trigger the subscription (e.g. changed attributes).
    """

    entities: List[EntityRef]
    condition: Optional[dict[str, Any]] = None


class NotificationHttp(BaseModel):
    """HTTP notification parameters.

    Parameters
    ----------
    url : str
        URL to send the notification to.
    """

    url: str = Field(..., min_length=1)


class Notification(BaseModel):
    """Subscription notification parameters.

    Parameters
    ----------
    http : NotificationHttp
        HTTP notification details.
    attrs : List[str], optional
        List of attributes to include in the notification.
    """

    http: NotificationHttp
    attrs: Optional[List[str]] = None


class Subscription(BaseModel):
    """Orion Context Broker subscription definition.

    Parameters
    ----------
    description : str
        Description of the subscription.
    subject : Subject
        Subject of the subscription (entities and conditions).
    notification : Notification
        Notification details (where and what to send).
    throttling : int, optional
        Minimum time between notifications in seconds.
    """

    description: str = Field(..., min_length=1)
    subject: Subject
    notification: Notification
    throttling: Optional[int] = None
