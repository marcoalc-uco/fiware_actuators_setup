"""Unit tests for the FIWARE Actuator microservice configuration.

These tests validate the creation of valid subscriptions beetwen orion and quantum leap.
"""

from fiware_actuators_setup.models.subscription import (
    EntityRef,
    Notification,
    NotificationHttp,
    Subject,
    Subscription,
)


def test_create_subscription():
    """Test the creation of a valid Subscription object."""
    subscription = Subscription(
        description="Notify QuantumLeap of all changes",
        subject=Subject(
            entities=[
                EntityRef(idPattern=".*", type="Device"),
            ],
            condition={"attrs": ["temperature"]},
        ),
        notification=Notification(
            http=NotificationHttp(
                url="http://quantumleap:8668/v2/notify",
            ),
            attrs=["temperature"],
        ),
        throttling=1,
    )

    assert subscription.description == "Notify QuantumLeap of all changes"
    assert len(subscription.subject.entities) == 1
    assert subscription.subject.entities[0].idPattern == ".*"
    assert subscription.subject.entities[0].type == "Device"
    assert subscription.notification.http.url == "http://quantumleap:8668/v2/notify"
    assert subscription.throttling == 1
