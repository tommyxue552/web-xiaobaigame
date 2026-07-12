# Crawler —— 独立采集服务

独立于主项目的游戏资源采集系统，负责从各游戏网站自动采集游戏信息。

## 目录结构

`
crawler/
├── base.py              # 采集器基类（Crawler）
├── requirements.txt     # Python 依赖
├── README.md            # 本文档
├── __init__.py          # 包入口
├── spiders/             # 采集规则（每个资源站一个 spider）
├── parser/              # 解析辅助工具
├── scheduler/           # 定时调度
└── logs/                # 运行日志
`

## 快速开始

### 1. 安装依赖

`ash
cd crawler
pip install -r requirements.txt
`

### 2. 编写一个 Spider

继承 Crawler 基类，实现 parse 方法：

`python
from crawler.base import Crawler

class MySpider(Crawler):
    source_name = "example"

    start_urls = [
        "https://example.com/games",
    ]

    def parse(self, html: str):
        # 用 BeautifulSoup 解析 HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        titles = [h2.text for h2 in soup.select("h2.game-title")]
        return titles
`

### 3. 运行采集

`python
from crawler.base import Crawler, RequestsEngine

spider = MySpider()
results = spider.run()

for r in results:
    print(r.url, r.status_code, r.success)
`

## 基类能力

Crawler 基类提供：

| 功能 | 说明 |
|------|------|
| etch(url) | 请求网页，返回 CrawlResult |
| un(urls) | 遍历 URL 列表，依次抓取并调用 parse |
| parse(html) | 抽象方法，子类实现解析逻辑 |
| process(item) | 钩子，处理单条解析结果 |
| 日志记录 | 内置 logging，输出到控制台和文件 |
| 异常处理 | 自动捕获网络异常、超时、解析异常 |

### 可配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| start_urls | [] | 起始 URL 列表 |
| equest_delay | 1.0 | 请求间隔（秒） |
| equest_timeout | 30 | 单次请求超时（秒） |
| extra_headers | {} | 额外请求头 |

## Playwright 扩展（预留）

当需要抓取 JS 渲染页面时，可使用 Playwright 引擎：

`python
from crawler.base import PlaywrightEngine

engine = PlaywrightEngine(headless=True)
spider = MySpider(engine=engine)
spider.run()
`

> 注意：PlaywrightEngine 为占位实现，需完成集成后使用。
> 使用前需执行 playwright install chromium。

## 日志

日志同时输出到控制台和 logs/crawler.log，在 ase.py 中统一配置。
