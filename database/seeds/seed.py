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
            # 检查游戏数据 - 更新已有数据的 images/download_url 字段
            existing_games = (await session.execute(select(Game))).scalars().all()
            if existing_games:
                print(f'[更新] 数据库中有 {len(existing_games)} 条游戏数据，补充下载链接字段')
                for g in existing_games:
                    if not g.images or g.images == []:
                        g.images = []
                    if not g.download_url:
                        g.download_url = 'https://store.steampowered.com/'
                    if not g.original_url:
                        g.original_url = g.download_url or ''
                await session.commit()
                print('[OK] 已补充下载链接和截图字段')
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
            images=['https://shared.steamstatic.com/store_item_assets/steam/apps/1245620/ss_ae44317e3bd07b7690b4d62cc5d0d1df30367a91.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/1245620/ss_e80a907c2c43337e53316c71555c3c3035a1343e.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/1245620/ss_7452c690f1b4ea06a2f072eb4b94e16a2c68fbff.600x338.jpg'],
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
            download_url='https://store.steampowered.com/app/1245620/',
            original_url='https://store.steampowered.com/app/1245620/',
            transfer_status='pending',
            publish_status='published',
        ),
        Game(
            title='荒野大镖客2',
            slug='red-dead-redemption-2',
            cover='',
            images=['https://shared.steamstatic.com/store_item_assets/steam/apps/1174180/ss_66b553f4c209476d3e4ce25e471e2e3d5808ac11.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/1174180/ss_bac60bacbf5da8945103648c08d27d5e202444ca.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/1174180/ss_668dafe4777438f70b36cf90d2ad5b32078a2338.600x338.jpg'],
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
            download_url='https://store.steampowered.com/app/1174180/',
            original_url='https://store.steampowered.com/app/1174180/',
            transfer_status='pending',
            publish_status='published',
        ),
        Game(
            title='星露谷物语',
            slug='stardew-valley',
            cover='',
            images=['https://shared.steamstatic.com/store_item_assets/steam/apps/413150/ss_ef179f1636dc779c7c3f2f153b68dbd6d3333e17.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/413150/ss_a0c5e158ec5a460aad40f7e3623e351a8cad3a3c.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/413150/ss_2c5785b601eebdab5232741edd95353ac8c08d6b.600x338.jpg'],
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
            download_url='https://store.steampowered.com/app/413150/',
            original_url='https://store.steampowered.com/app/413150/',
            transfer_status='pending',
            publish_status='published',
        ),
        Game(
            title='文明6',
            slug='civilization-6',
            cover='',
            images=['https://shared.steamstatic.com/store_item_assets/steam/apps/289070/ss_f501156a69223131ee5b39a15d7896653cb4a0d5.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/289070/ss_36c63eb1420064a7a3d55a59b5e2e832a3128798.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/289070/ss_fced5d740adcfc70bcd6b5b77f5c6dbecc914d7a.600x338.jpg'],
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
            download_url='https://store.steampowered.com/app/289070/',
            original_url='https://store.steampowered.com/app/289070/',
            transfer_status='pending',
            publish_status='published',
        ),
        Game(
            title='空洞骑士',
            slug='hollow-knight',
            cover='',
            images=['https://shared.steamstatic.com/store_item_assets/steam/apps/367520/ss_d5b6edd94e7471e9b7e7ad0e6e9fc1b35e89feae.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/367520/ss_20f82b1c6606aae19b7a2eb0fa0dff7926a6a852.600x338.jpg',
                     'https://shared.steamstatic.com/store_item_assets/steam/apps/367520/ss_b69fd6f41a78c43a23aaac2f0b5beffea9423216.600x338.jpg'],
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
            download_url='https://store.steampowered.com/app/367520/',
            original_url='https://store.steampowered.com/app/367520/',
            transfer_status='pending',
            publish_status='published',
        ),
    ]
    session.add_all(games)
    await session.commit()
    print(f'[OK] 插入 {len(games)} 条测试游戏数据')


if __name__ == '__main__':
    asyncio.run(seed())
