<h1 align="center">twikit</h1>

<p align="center">
  一个无需 <b>API 密钥</b> 的 Python <b>Twitter / X</b> 抓取库。<br>
  它是 <a href="https://github.com/d60/twikit">d60/twikit</a> 的分支，并入了 <a href="https://github.com/PawiX25/twifork">PawiX25/twifork</a> 的修复与新增功能（让上游在 2026 年无法正常使用的那些问题的修复、X Spaces 支持等）。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/github/stars/amanetoki7/twikit?style=flat&color=yellow" alt="Stars">
</p>

<p align="center">
  [<a href="README.md">日本語</a>] · [<a href="README-en.md">English</a>] · [中文]
</p>

> **可直接替换。** 包名和导入名仍然是 `twikit`，所以 `from twikit import Client` 这类现有代码无需改动即可继续使用。

---

## 安装

本仓库没有发布到 PyPI，请直接从 git 安装：

```bash
pip install git+https://github.com/amanetoki7/twikit.git
```

> [!WARNING]
> `pip install twikit` 装到的是上游（d60/twikit）的 `2.3.3`，截至 2026 年它已经有多处无法使用，并且不包含本仓库的任何修复。

可选功能通过 extras 指定：

```bash
# 浏览器 TLS 指纹伪装，绕过部分 403（curl_cffi）
pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"

# X Spaces 的 WebRTC 语音（发言 / 收听）与实时聊天 WebSocket（aiortc + websockets）
pip install "twikit[spaces] @ git+https://github.com/amanetoki7/twikit.git"
```

从克隆的仓库进行开发：

```bash
git clone https://github.com/amanetoki7/twikit.git
cd twikit
pip install -e ".[impersonate,spaces]"
```

需要 **Python 3.10 或更高版本**（代码使用了 `anext()` 和字典的 `|` 运算符）。

## 相对上游修复了什么

上游的 PyPI 版本（`twikit==2.3.3`）在 2026 年已经有多处无法使用。本仓库并入了 twifork 的修复，这些问题全部已经解决。下面每一项都链接到对应的上游 Issue：

- **ClientTransaction / `Couldn't get KEY_BYTE indices`** — 按 X 新的 webpack 打包结构更新了 `ondemand.s.js` 的解析，GraphQL 请求重新可用。([#408](https://github.com/d60/twikit/issues/408)、[#409](https://github.com/d60/twikit/issues/409)、[#304](https://github.com/d60/twikit/issues/304))
- **`SearchTimeline` 和 `friends/list` 上时有时无、且会"卡住"的 `404`** — 计算 `x-client-transaction-id` 的动画密钥时漏掉了 X 的 `frame_time` 取整步骤，导致某些 `Client` 会话在重新创建之前，所有严格校验的请求都会返回 404。修复之后，这种随机 404 就消失了。([#357](https://github.com/d60/twikit/issues/357)、[#397](https://github.com/d60/twikit/issues/397))
- **可选字段缺失时的 `KeyError`**（`User.__init__` 与 `Client.request`）— 改用 `.get()` 安全读取。([#417](https://github.com/d60/twikit/issues/417))
- **用户 `name` / `screen_name` 为空**（常见于搜索结果）— X 把 `name`、`screen_name`、`created_at`、头像、位置等字段从 `legacy` 移到了新的子对象，现在会读取新位置并回退到 `legacy`。
- **`get_tweet_by_id` 的 `KeyError: 'itemContent'`** — 同时兼容旧版和新版的末尾游标结构。([#332](https://github.com/d60/twikit/issues/332)、[#363](https://github.com/d60/twikit/issues/363))
- **没有可见推文的账户上，`get_user_tweets` 的 `KeyError: 'entries'` / `IndexError`** — 空的、没有游标的时间线会返回空结果，而不再崩溃。([#361](https://github.com/d60/twikit/issues/361)、[#216](https://github.com/d60/twikit/issues/216))
- **`get_trends` 被弃用、什么都不返回** — 基于 `GenericTimelineById` 重写，并新增了 `get_explore_page()`。([#389](https://github.com/d60/twikit/issues/389))
- **限流时的 `RecursionError`** — 429 的恢复逻辑不再递归。
- **`GuestClient` 无法使用，而且这不是库能修的。** `User-Agent` 头和防御性的用户字段解析都已就位（[#402](https://github.com/d60/twikit/issues/402)、[#385](https://github.com/d60/twikit/issues/385)），但 `activate()` 根本走不到那一步。对线上 X 的验证结果是：所有请求都先经过 `x-client-transaction-id` 握手，而未登录的请求只能拿到一个约 34 KB、不含 webpack 清单的页面外壳，握手无法完成，`activate()` 本身就会抛出 `InvalidSession`。`/1.1/guest/activate.json` 端点还活着，只是到不了。游客访问已被 X 关闭，请使用 cookie。([#192](https://github.com/d60/twikit/issues/192))
- **`get_latest_friends` 的 404** — 在 v1.1 端点下线后，改走 GraphQL 的 `Following` 端点。([#397](https://github.com/d60/twikit/issues/397))
- **`'Client' object has no attribute '_ui_metrix'`** — 修复了验证码解锁流程。([#333](https://github.com/d60/twikit/issues/333))
- **`get_bookmark_folders().next()` 死循环** — 修正了写错的分页参数。([#334](https://github.com/d60/twikit/issues/334)、[#335](https://github.com/d60/twikit/issues/335))
- **`get_latest_timeline` / `get_list_tweets` 漏掉会话推文** — 现在会展开 home / list 的会话条目。([#336](https://github.com/d60/twikit/issues/336)、[#337](https://github.com/d60/twikit/issues/337)、[#340](https://github.com/d60/twikit/issues/340))
- 新增用于获取原图的 **`Media.source_url`**（[#376](https://github.com/d60/twikit/issues/376)），以及返回被引用推文 ID 的 **`Tweet.quoted_status_id`**（[#222](https://github.com/d60/twikit/issues/222)）。

### 其他修复

除上述列表之外，还并入了 twifork 提交历史中的这些修复：

- **`import twikit` 不再改写整个进程** — 以前在 Windows 上会替换事件循环策略，导致同时需要子进程的库（playwright 等）抛出 `NotImplementedError`。确实需要旧行为时，设置环境变量 `TWIKIT_WINDOWS_SELECTOR_LOOP=1`。
- **分页** — X 不返回游标时，`next()` / `previous()` 不再反复请求同一页；`get_lists` 遇到没有列表的页面也会继续翻页。`count` 会被遵守，X 多给的部分通过 `next()` 返回。
- **`impersonate=` 下的请求** — 以前会丢掉 `json=` 请求体和 `files=`（媒体分块），导致 GraphQL 的 POST（时间线、`create_tweet`）返回 422、`upload_media` 失败。同时修复了 cookie 被发到无关主机、旧的 `auth_token` 残留在其他域名下、以及 `twitter.com` 的 csrf cookie 在第一次响应后消失的问题。
- **回复标签页与私信** — `get_user_tweets(..., 'Replies')` 返回的是对方的推文而不是用户自己的回复；置顶推文被漏掉或重复；`send_dm` 报告了错误的发送者。这些都已修复。
- **不再隐藏 X 的拒绝** — 权限错误（代码 37 等）不再以空结果返回，`create_tweet` 会原样显示 X 的每日上限提示，找不到的列表 / 用户会抛出 `NotFound` / `UserNotFound` 而不是返回空对象。
- **通知** — `get_notifications('Mentions')` 支持不含 `notifications` 键的新结构。
- **`get_trends`** — 不再无限重试，news / sports / entertainment 分类也不再返回空。
- **X 从 `legacy` 移走的字段** — User / Community / 多图的 `Tweet.media` / 转推的全文 / 进行中的投票都会从新位置读取。`Poll.vote` 现在也接受选项序号（破坏性变更）。
- **新增属性** — `Tweet.url`、`Tweet.article`（`Article`）、`Tweet.source`、`Tweet.conversation_ids`、`User.verified_type`、恶搞 / 自动化标签、`Conversation`、`Message.reply_data` 等。`Tweet.urls` 始终返回列表。
- **登录** — 登录挑战可以按任意顺序处理，`code_callback` 取代了会阻塞事件循环的 `input()`。不过密码登录本身已被 X 下线，会抛出 `LoginRetired`（见下文）。
- **`x-client-transaction-id` 握手** — 串行化、失败时重试，并在 cookie 变化后丢弃旧握手。长期运行的进程可以调用 `client.refresh_transaction()`。
- **端点** — GraphQL 的 query id 与 feature 标志更新到 2026 年的值；用户资料查询保留了仍会返回 `listed_count` 等 legacy 计数的文档。
- **打包** — 声明了真实的 Python 下限（3.10），随包附带 `py.typed`，并固定 `httpx>=0.26`。`twikit.errors` 的模块文档记录了实际观察到的 X 错误代码和间歇性 404 的原因。

至于由 X 一侧限制引起的问题（账户封禁、Cloudflare / IP 封锁、验证码、自动化限制），库本身无能为力，不在本项目范围内。

### 浏览器 TLS 伪装（可选）

X 的某些端点即使请求本身没问题，也会用 `403`（HTML 页面）拒绝 `httpx` 默认的 TLS 指纹。安装可选的 `curl_cffi` 后端并传入 `impersonate=`，请求就会以真实浏览器的 TLS 指纹发出，从而避开这类 403。

```python
client = Client('zh-cn', impersonate='chrome124')
```

## 快速上手

> [!IMPORTANT]
> **请用 cookie 登录，不要用密码。**
> X 已经下线了 `Client.login()` 所依赖的 onboarding 流程，它会返回 `code 366, "flow name LoginFlow is currently not accessible"`。2026-07-29 对线上 x.com 的验证结果：`/i/flow/login` 会重定向到 `/i/jf/onboarding/web`，网站会向 `/i/jfapi/onboarding/web/actions/begin_login` 发送 POST，该请求需要由页面内混淆 JavaScript 生成的约 5 KB 的 `$castle_token`，并把 passkey / WebAuthn 作为第一因素提供。这些都无法从普通的 HTTP 客户端触达，因此**密码登录无法实现**，库层面的修复也无济于事。请改为导出浏览器会话中的 cookie。

**获取 cookie**：在浏览器中登录 x.com，打开开发者工具（Application / Storage → Cookies），复制 `auth_token` 和 `ct0` 的值。这两个就够了。

**创建客户端并载入 cookie。**

```python
import asyncio
from twikit import Client

# impersonate= 需要 extras：pip install "twikit[impersonate] @ git+https://github.com/amanetoki7/twikit.git"
# 没有它，v1.1 端点可能会连同 Cloudflare 页面一起返回 403。
client = Client('zh-cn', impersonate='chrome124')

async def main():
    # auth_token 和 ct0 就够了
    client.set_cookies({'auth_token': '...', 'ct0': '...'})
    # 或者：client.load_cookies('cookies.json')

    if not await client.is_logged_in():
        raise SystemExit('cookie 已失效，请重新导出。')

    # 保存起来供下次使用
    client.save_cookies('cookies.json')

asyncio.run(main())
```

`set_cookies` 也接受浏览器扩展或 Playwright 导出的列表格式（由带 `name` 和 `value` 的字典组成的列表）。

**发布带图片的推文。**

```python
media_ids = [
    await client.upload_media('media1.jpg'),
    await client.upload_media('media2.jpg'),
]
await client.create_tweet(text='Example Tweet', media_ids=media_ids)
```

**按关键词搜索最新推文。**

```python
tweets = await client.search_tweet('python', 'Latest')
for tweet in tweets:
    print(tweet.user.name, tweet.text, tweet.created_at)
```

**其他常用调用。**

```python
await client.get_user_tweets('123456', 'Tweets')   # 某个用户的推文
await client.send_dm('123456789', 'Hello')          # 发送私信
await client.get_trends('trending')                 # 热门趋势
```

更多示例：[examples](examples)

## 特性

- **无需 API 密钥** — 通过抓取网页端工作。
- **免费、开源**（MIT）。
- **`twikit` 的直接替换** — 导入名相同，代码无需改动。
- 推文、搜索、时间线、趋势、用户、私信、媒体、书签等等。
- **X Spaces** — 读取、搜索、创建、发布、管理和结束语音空间，HLS 流地址，聊天记录和实时聊天。核心流程不需要额外的包（`twikit[spaces]` 提供 WebRTC 语音和实时聊天 WebSocket）。参见 [docs/spaces.rst](docs/spaces.rst) 和 [examples/spaces.py](examples/spaces.py)：

  ```python
  space = await client.spaces.get_space('1DXGydznBYWKM')
  stream = await client.spaces.get_stream(space.media_key)   # HLS 地址
  chat = await client.spaces.chat(space)                     # 聊天记录
  created = await client.spaces.create_space(title='hi')     # 开始直播
  await client.spaces.end_space(created['broadcast']['id'])
  ```

### 相对上游新增的 API

- `Client(impersonate=...)` — 通过 curl_cffi 伪装浏览器 TLS 指纹。
- `Client.is_logged_in()` — 检查 cookie 是否仍然有效。
- `Client.rate_limit_remaining` / `Client.rate_limit_reset` — 最近一次响应中报告的限流余量和重置时间。
- `Client.refresh_transaction()` — 重新进行 `x-client-transaction-id` 握手。
- `Client.get_dm_inbox()`、`create_group()`、`delete_dm_conversation()` — 私信收件箱、创建群组、删除会话。
- `Client.update_profile()`、`get_about_account()`、`get_user_spotlights()`、`get_user_lists()`、`get_muted_users()`、`get_blocked_users()`。
- `Client.get_user_mentions()`、`search_tweets_by_date()`、`get_thread()`、`get_tweet_by_url()`、`get_explore_page()`。
- `twikit.SearchOptions` / `twikit.build_query` — 构建搜索查询。
- `twikit.Article`、`twikit.Conversation` — 长文与私信会话。
- `twikit.spaces` — Spaces 相关的类（`Spaces`、`Space`、`SpaceChat`、`SpaceVoiceSession` 等）。
- 异常：`ClientTransactionError`、`InvalidSession`（cookie 被拒绝）、`LoginRetired`（密码登录已下线）。

## 文档

本仓库的文档以日语编写。

- API 参考（Sphinx）：[docs/twikit.rst](docs/twikit.rst)。在 `docs/` 目录下执行 `make html` 即可构建（`pip install -r docs/requirements.txt`）。
- Spaces 指南：[docs/spaces.rst](docs/spaces.rst)
- 限流说明：[ratelimits.md](ratelimits.md)
- 保护你的账户：[ToProtectYourAccount.md](ToProtectYourAccount.md)
- 上游 API 参考（英文；本仓库是它的超集）：https://twikit.readthedocs.io/en/latest/twikit.html

## 社区

上游 twikit 的 Discord：[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)

## 参与贡献

发现 bug 或者有修复方案？欢迎到 [amanetoki7/twikit](https://github.com/amanetoki7/twikit/issues) 提交 Issue 或 Pull Request。

如果它帮你省了麻烦，欢迎点个 ⭐。

## 致谢

- **[d60/twikit](https://github.com/d60/twikit)**（[@d60](https://github.com/d60)）— 原始实现，全部功劳归原作者所有。
- **[PawiX25/twifork](https://github.com/PawiX25/twifork)**（[@PawiX25](https://github.com/PawiX25) 及贡献者们）— 2026 年的修复与 X Spaces 支持，本仓库在其基础上构建。

两者均基于 **MIT 许可证**发布。

## 免责声明

本项目是一个独立的非官方项目，**与 X Corp. 不存在任何隶属、认可或赞助关系。**"X" 和 "Twitter" 是 X Corp. 的商标。请在遵守相关条款和法律的前提下使用。
