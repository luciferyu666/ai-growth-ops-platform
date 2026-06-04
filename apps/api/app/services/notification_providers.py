import logging
from dataclasses import dataclass, field
from typing import Protocol

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationPayload:
    channel: str
    recipient: str
    subject: str | None
    body: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class NotificationProviderResult:
    success: bool
    provider_message_id: str | None = None
    retryable: bool = False
    error_message: str | None = None
    metadata: dict = field(default_factory=dict)


class NotificationProvider(Protocol):
    name: str

    def send(self, payload: NotificationPayload) -> NotificationProviderResult:
        """Send a notification payload through a concrete provider."""


class MockNotificationProvider:
    name = "mock"

    def send(self, payload: NotificationPayload) -> NotificationProviderResult:
        if payload.metadata.get("force_permanent_fail") is True or (
            payload.recipient.endswith("@dead.test")
        ):
            return NotificationProviderResult(
                success=False,
                retryable=False,
                error_message="Mock notification provider rejected the message permanently",
                metadata={"provider": self.name, "failure_mode": "permanent"},
            )

        if payload.metadata.get("force_fail") is True or (
            payload.recipient.endswith("@fail.test")
        ):
            return NotificationProviderResult(
                success=False,
                retryable=True,
                error_message="Mock notification provider reported a retryable failure",
                metadata={"provider": self.name, "failure_mode": "retryable"},
            )

        return NotificationProviderResult(
            success=True,
            provider_message_id=f"mock-{payload.metadata.get('notification_id')}",
            metadata={"provider": self.name, "delivery_mode": "simulated"},
        )


class ConsoleNotificationProvider:
    name = "console"

    def send(self, payload: NotificationPayload) -> NotificationProviderResult:
        logger.info(
            "notification.console.delivered",
            extra={
                "recipient": payload.recipient,
                "channel": payload.channel,
                "subject": payload.subject,
            },
        )
        return NotificationProviderResult(
            success=True,
            provider_message_id=f"console-{payload.metadata.get('notification_id')}",
            metadata={"provider": self.name, "delivery_mode": "console"},
        )


def get_notification_provider(provider_name: str | None = None) -> NotificationProvider:
    provider_name = (
        provider_name or get_settings().notification_provider
    ).strip().lower()
    if provider_name == "console":
        return ConsoleNotificationProvider()
    return MockNotificationProvider()
