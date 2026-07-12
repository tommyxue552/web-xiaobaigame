# -*- coding: utf-8 -*-
"""
???????
-------------
??????????????????????
?????python database/seeds/seed.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from backend.app.core.database import async_session_factory, init_db
from backend.app.core.auth import hash_password
from backend.app.models.admin_user import AdminUser
from backend.app.models.category import Category
from sqlalchemy import select


ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

DEFAULT_CATEGORIES = [
    ("????", "action"),
    ("????", "rpg"),
    ("????", "adventure"),
    ("????", "simulation"),
    ("????", "strategy"),
    ("????", "shooter"),
    ("????", "casual"),
]


async def seed():
    await init_db()

    async with async_session_factory() as db:
        # ???????
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == ADMIN_USERNAME)
        )
        existing_admin = result.scalar_one_or_none()
        if not existing_admin:
            admin = AdminUser(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
            )
            db.add(admin)
            print(f"[??] ????????: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        else:
            print(f"[??] ???????????")

        # ??????
        for name, slug in DEFAULT_CATEGORIES:
            result = await db.execute(
                select(Category).where(Category.slug == slug)
            )
            if not result.scalar_one_or_none():
                cat = Category(name=name, slug=slug)
                db.add(cat)
                print(f"[??] ?????: {name} ({slug})")
            else:
                print(f"[??] ????????: {name}")

        await db.commit()

    print("[??] ???????")


if __name__ == "__main__":
    asyncio.run(seed())
