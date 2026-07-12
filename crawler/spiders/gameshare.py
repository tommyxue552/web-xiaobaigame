# -*- coding: utf-8 -*-
"""
GameshareSpider —— 游戏分享站采集器
================================
采集 3DM 游戏下载站的游戏资源列表。
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from ..base import Crawler


class GameshareSpider(Crawler):
    """3DM 下载站采集器。

    采集目标：https://dl.3dmgame.com
    解析逻辑：从游戏列表页的 div.item 卡片中提取信息。
    """

    source_name: str = "gameshare"

    # 起始 URL —— 列表首页 + 前几页分页
    start_urls: list[str] = [
        "https://dl.3dmgame.com",
        "https://dl.3dmgame.com/all_all_2_time/",
        "https://dl.3dmgame.com/all_all_3_time/",
    ]

    request_delay: float = 2.0

    # ------------------------------------------------------------------
    # 解析逻辑
    # ------------------------------------------------------------------

    def parse(self, html: str) -> list[dict[str, str]]:
        """从游戏列表页 HTML 中提取游戏条目。

        返回结构化列表，每项包含：
            title, cover, description, category, size,
            download_url, original_url, source
        """
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.item")
        items: list[dict[str, str]] = []

        for card in cards:
            # ---- 标题 & URL ----
            title_el = card.select_one("div.bt a")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            original_url = title_el.get("href", "")

            if not title or not original_url:
                continue

            # ---- 封面 ----
            cover = ""
            img_el = card.select_one("div.img img")
            if img_el:
                cover = img_el.get("data-original") or img_el.get("src") or ""

            # ---- 分类 (类型) ----
            category = ""
            type_li = card.select_one("ol li i")
            if type_li:
                category = type_li.get_text(strip=True)

            # ---- 平台 / 语言 / 评分 等作为描述 ----
            info_parts: list[str] = []
            for li in card.select("ol li"):
                label = li.get_text(strip=True)
                if label:
                    info_parts.append(label)
            description = "；".join(info_parts) if info_parts else ""

            # ---- 大小 ----
            size = ""
            dl_el = card.select_one("a.a_click")
            if dl_el:
                dl_text = dl_el.get_text(strip=True)
                size_match = re.search(
                    r"[\d.]+(?:GB|MB|KB|gb|mb|kb|G|M|K)", dl_text
                )
                if size_match:
                    size = size_match.group(0)

            # ---- 下载链接 ----
            download_url = ""
            if dl_el:
                download_url = dl_el.get("href", "")

            items.append({
                "title": title,
                "cover": cover,
                "description": description,
                "category": category,
                "size": size,
                "download_url": download_url,
                "original_url": original_url,
                "source": self.source_name,
            })

        return items

    # ------------------------------------------------------------------
    # 处理钩子
    # ------------------------------------------------------------------

    def process(self, items: Any) -> None:
        """将解析结果存入实例变量，供外部收集。"""
        if isinstance(items, list):
            if not hasattr(self, "_collected"):
                self._collected: list[dict[str, str]] = []
            self._collected.extend(items)
        super().process(items)

    @property
    def collected_items(self) -> list[dict[str, str]]:
        """获取本次运行收集到的所有游戏条目。"""
        return getattr(self, "_collected", [])
