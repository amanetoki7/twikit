<h1 align="center">twikit（C# 版）</h1>

<p align="center">
  <b>API キー不要</b>で使える、.NET 向けの <b>Twitter / X</b> API クライアントライブラリ。<br>
  Python 版 <a href="../README.md">twikit</a>（d60/twikit に PawiX25/twifork の 2026 年時点の修正と X スペース対応を取り込んだフォーク）を、そのまま C# に移植したものです。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/.NET-8.0%2B-512BD4" alt=".NET 8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
</p>

> **Python 版と同じ構造・同じ挙動。** メソッド名は C# の慣習（PascalCase、`...Async`）に置き換えただけなので、Python 版のコードはそのまま読み替えられます。対応表は [docs/articles/python-differences.md](docs/articles/python-differences.md) を参照してください。

---

## 構成

| パス | 内容 |
|---|---|
| [`Twikit/`](Twikit) | ライブラリ本体（`net8.0`、NuGet: AngleSharp, Jint） |
| [`Twikit.Tests/`](Twikit.Tests) | xunit のテスト。`X-Client-Transaction-Id` の計算は Python 版で生成したフィクスチャと bit 単位で一致することを確認しています |
| [`examples/Twikit.Examples/`](examples/Twikit.Examples) | Python 版の `examples/*.py` に対応するサンプル |
| [`docs/`](docs) | DocFX のドキュメント（日本語）。`docfx docs/docfx.json --serve` でローカルに表示できます |

## インストール

NuGet には公開していません。リポジトリを clone してプロジェクト参照で使ってください。

```bash
git clone https://github.com/amanetoki7/twikit.git
```

```xml
<ItemGroup>
  <ProjectReference Include="path/to/twikit/csharp/Twikit/Twikit.csproj" />
</ItemGroup>
```

パッケージとして配布する場合は `dotnet pack csharp/Twikit/Twikit.csproj -c Release` で `.nupkg` を作れます。**.NET 8 以上**が必要です。

## 使い方

> [!IMPORTANT]
> **パスワードではなく Cookie でログインしてください。**
> X は `Client.LoginAsync()` が使うオンボーディングフローを廃止しており、`code 366, "flow name LoginFlow is currently not accessible"` を返します。パスワードログインはライブラリ側では直せません（`LoginRetiredException` になります）。ブラウザでログインしたセッションの Cookie を取り出して使ってください。

**Cookie の取り出し方**: ブラウザで x.com にログインし、開発者ツール（Application / Storage → Cookies）から `auth_token` と `ct0` の値をコピーします。この 2 つだけで十分です。

**クライアントを用意して Cookie をセットする。**

```csharp
using Twikit;

var client = new Client("ja");

// auth_token と ct0 だけで十分です
client.SetCookies(new Dictionary<string, string> { ["auth_token"] = "...", ["ct0"] = "..." });
// または: client.LoadCookies("cookies.json");

if (!await client.IsLoggedInAsync())
    throw new Exception("Cookie が無効です。ブラウザから取り直してください。");

// 次回以降のために保存しておく
client.SaveCookies("cookies.json");
```

`SetCookies` には、ブラウザの拡張機能や Playwright が書き出す形式（`name` と `value` を持つオブジェクトの配列）も `JsonNode` として渡せます。

**メディア付きツイートを投稿する。**

```csharp
var mediaIds = new List<string>
{
    await client.UploadMediaAsync("media1.jpg"),
    await client.UploadMediaAsync("media2.jpg"),
};
await client.CreateTweetAsync("Example Tweet", mediaIds);
```

**キーワードで最新のツイートを検索する。**

```csharp
var tweets = await client.SearchTweetAsync("python", "Latest");
foreach (var tweet in tweets)
    Console.WriteLine($"{tweet.User?.Name}: {tweet.Text} ({tweet.CreatedAt})");

var more = await tweets.NextAsync();   // 続きを取得
```

**その他、よく使う呼び出し。**

```csharp
await client.GetUserTweetsAsync("123456", "Tweets");   // ユーザーのツイート
await client.SendDmAsync("123456789", "Hello");         // DM を送る
await client.GetTrendsAsync("trending");                // トレンド
```

さらに詳しい例は [examples/Twikit.Examples](examples/Twikit.Examples) にあります。

```bash
AUTH_TOKEN=... CT0=... dotnet run --project csharp/examples/Twikit.Examples -- basic
```

## 主な機能

- **API キー不要** — Web 版をスクレイピングして動作します。
- ツイート、検索、タイムライン、トレンド、ユーザー、DM、メディア、ブックマーク、リスト、コミュニティ、通知、ストリーミングなど、Python 版のすべての公開 API。
- **X スペース（Spaces）** — 読み取り・検索・作成・公開・モデレーション・終了、HLS ストリーム URL、チャット履歴・ライブチャット（WebSocket）。

  ```csharp
  var space = await client.Spaces.GetSpaceAsync("1DXGydznBYWKM");
  var stream = await client.Spaces.GetStreamAsync(space.MediaKey!);        // HLS URL
  var chat = await client.Spaces.ChatAsync(space);                          // 履歴
  var created = await client.Spaces.CreateSpaceAsync(title: "こんにちは");   // ライブ開始
  await client.Spaces.EndSpaceAsync(created["broadcast"]!["id"]!.GetValue<string>());
  ```

## Python 版との違い

- **`impersonate=`（curl_cffi による TLS 偽装）はありません。** .NET 標準に相当する仕組みが無いため、代わりに `new Client(handler: ...)` で独自の `HttpMessageHandler` を差し込めます。
- **X スペースの音声（WebRTC）** は、.NET 標準に WebRTC 実装が無いため `IPeerConnection` / `IPeerConnectionFactory` インターフェイスを用意しています（SIPSorcery などで実装して `SpeakAsync` / `HostAsync` / `ListenAsync` に渡します）。メタデータ・検索・作成・終了・モデレーション・チャットは実装無しで動作します。
- **`List` は `TwitterList`** という名前です（`System.Collections.Generic.List<T>` との混同を避けるため）。
- 例外は `...Exception` 付きの名前（`NotFoundException` など）。基底クラスは Python 版と同じ `TwitterException` です。
- `GuestClient` も移植していますが、Python 版と同じく X 側でゲストアクセスが閉じられているため `ActivateAsync()` は `InvalidSessionException` になります。

そのほかの細かな差異は [docs/articles/python-differences.md](docs/articles/python-differences.md) にまとめています。

## ドキュメント

[DocFX](https://dotnet.github.io/docfx/) で日本語のドキュメントを生成できます。API リファレンスはソースコードの XML ドキュメントコメント（日本語）から作られます。

```bash
dotnet tool install -g docfx
docfx csharp/docs/docfx.json --serve   # http://localhost:8080
```

`main` に push すると [`.github/workflows/docs.yml`](../.github/workflows/docs.yml) がサイトをビルドして GitHub Pages に公開します（リポジトリの Settings → Pages → Source を "GitHub Actions" にしておいてください）。

- [はじめに](docs/articles/getting-started.md)
- [Python 版との対応](docs/articles/python-differences.md)
- [X スペース](docs/articles/spaces.md)
- [レート制限](docs/articles/ratelimits.md) / [アカウントを守るために](docs/articles/protect-account.md) / [エラー](docs/articles/errors.md)

## ビルドとテスト

```bash
cd csharp
dotnet build Twikit.sln -c Release
dotnet test Twikit.Tests -c Release
```

テストはネットワークに接続しません。`X-Client-Transaction-Id` の計算（アニメーションキー、`float_to_hex`、3 次ベジェ、Python 互換の丸め）は、Python 版の実装で生成した `Twikit.Tests/Fixtures` の値と一致することを確認しています。

## アカウントを守るために

このライブラリは非公式 API を使うため、使い方を誤るとアカウントが凍結される可能性があります。リクエストを送りすぎない、Cookie を使い回す、といった対策を [docs/articles/protect-account.md](docs/articles/protect-account.md) にまとめています。

## クレジット

- **[d60/twikit](https://github.com/d60/twikit)**（[@d60](https://github.com/d60)）— 元になる実装。
- **[PawiX25/twifork](https://github.com/PawiX25/twifork)** — 2026 年時点の不具合修正と X スペース対応。
- `X-Client-Transaction-Id` の計算は [iSarabjitDhiman/TweeterPy](https://github.com/iSarabjitDhiman/TweeterPy) に由来します。

いずれも **MIT ライセンス**で公開されています。

## 免責事項

このリポジトリは独立した非公式プロジェクトであり、**X Corp. とは一切の提携・承認・スポンサー関係はありません。**「X」および「Twitter」は X Corp. の商標です。利用にあたっては、適用される規約および法令を守ってください。
