"""Promote an existing user to platform admin.

Platform admin is a cross-org superuser and is never granted by self-signup.
Run this server-side against a real registered account:

    python -m app.make_platform_admin someone@example.com
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models import User


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m app.make_platform_admin <email>")
        raise SystemExit(2)
    email = sys.argv[1].strip().lower()
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == email))
        if not user:
            print(f"No user found with email {email!r}")
            raise SystemExit(1)
        user.role = "platform_admin"
        user.org_id = None
        session.commit()
        print(f"{email} is now a platform_admin (org detached).")


if __name__ == "__main__":
    main()
