"""Outbound email — stub implementation.

A real product needs transactional email (verification, password reset, invites).
Until a provider is wired, `send_email` just logs to stdout so the flows work
end-to-end in development without an external dependency. Swap the body of
`send_email` for a real provider later without changing callers.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("confusionlayer.mail")


def send_email(to: str, subject: str, body: str) -> None:
    logger.info("[stub-email] to=%s subject=%s\n%s", to, subject, body)
    # Also print so it is visible in container logs during development.
    print(f"[stub-email] to={to} subject={subject}\n{body}", flush=True)
