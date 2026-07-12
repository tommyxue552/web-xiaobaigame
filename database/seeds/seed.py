"""
种子数据脚本
-----------
插入 7 条分类 + 5 条测试游戏数据。
运行方式：python database/seeds/seed.py
"""

import sys
import os
import asyncio

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.app.core.database import engine, async_session_factory, Base
from backend.app.models.game import Game
from backend.app.models.category import Category
from sqlalchemy import select


async def seed():
    # 先建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # 检查是否已有数据
        existing = (await session.execute(select(Category))).scalars().all()
        if existing:
            print('[跳过] 数据库中已有分类数据，不再重复插入')
            # 检查游戏数据
            existing_games = (await session.execute(select(Game))).scalars().all()
            if existing_games:
                print(f'[跳过] 数据库中已有 {len(existing_games)} 条游戏数据')
            else:
                await insert_games(session)
            return

        # 插入分类
        categories = [
            Category(name='动作游戏', slug='action'),
            Category(name='角色扮演', slug='rpg'),
            Category(name='冒险游戏', slug='adventure'),
            Category(name='模拟经营', slug='simulation'),
            Category(name='策略游戏', slug='strategy'),
            Category(name='射击游戏', slug='shooter'),
            Category(name='休闲游戏', slug='casual'),
        ]
        session.add_all(categories)
        await session.flush()
        print(f'[OK] 插入 {len(categories)} 条分类数据')

        # 插入游戏
        await insert_games(session)

    print('[完成] 种子数据初始化完毕')


async def insert_games(session):
    games = [
        Game(
            title='艾尔登法环',
            slug='elden-ring',
            cover='',
            description='艾尔登法环是以正统黑暗奇幻世界为舞台的动作RPG游戏。走进辽阔的场景与地下迷宫探索未知，挑战困难重重的险境。',
            system='Windows',
            language='中文',
            size='48.6GB',
            version='v1.10',
            publisher='Bandai Namco',
            developer='FromSoftware',
            category='动作游戏',
            category_id=1,
            tags=['魂系', '开放世界', '奇幻'],
            publish_status='published',
        ),
        Game(
            title='荒野大镖客2',
            slug='red-dead-redemption-2',
            cover='',
            description='Rockstar Games 出品的史诗级开放世界游戏，带你领略狂野西部的最后岁月。',
            system='Windows',
            language='中文',
            size='119.5GB',
            version='v1.0.1436.28',
            publisher='Rockstar Games',
            developer='Rockstar Studios',
            category='冒险游戏',
            category_id=3,
            tags=['开放世界', '西部', '剧情'],
            publish_status='published',
        ),
        Game(
            title='星露谷物语',
            slug='stardew-valley',
            cover='',
            description='你继承了爷爷在星露谷留下的老旧农场。带着爷爷留下的残旧工具和几枚硬币开始了你的新生活。',
            system='Windows',
            language='中文',
            size='560MB',
            version='v1.6.8',
            publisher='ConcernedApe',
            developer='ConcernedApe',
            category='模拟经营',
            category_id=4,
            tags=['农场', '像素', '休闲', '多人'],
            publish_status='published',
        ),
        Game(
            title='文明6',
            slug='civilization-6',
            cover='',
            description='《文明VI》是屡获殊荣的回合制策略游戏系列新作。扩张帝国疆域，提升文化水平，与历史上最伟大的领袖们竞争。',
            system='Windows',
            language='中文',
            size='12.8GB',
            version='v1.0.12.58',
            publisher='2K Games',
            developer='Firaxis Games',
            category='策略游戏',
            category_id=5,
            tags=['回合制', '历史', '4X'],
            publish_status='published',
        ),
        Game(
            title='空洞骑士',
            slug='hollow-knight',
            cover='',
            description='在《空洞骑士》中开拓自己的道路！穿越一个广阔且相互关联的失落王国，与受感染的生物战斗，结识奇异的虫子。',
            system='Windows',
            language='中文',
            size='3.8GB',
            version='v1.5.78.11833',
            publisher='Team Cherry',
            developer='Team Cherry',
            category='动作游戏',
            category_id=1,
            tags=['类银河城', '手绘', '独立游戏'],
            publish_status='published',
        ),
    ]
    session.add_all(games)
    await session.commit()
    print(f'[OK] 插入 {len(games)} 条测试游戏数据')


if __name__ == '__main__':
    asyncio.run(seed())
