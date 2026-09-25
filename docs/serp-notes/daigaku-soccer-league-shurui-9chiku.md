# SERP分析メモ: 「大学サッカー リーグ 種類」（H／上位クエリ）

- 調査日: 2026-09-23
- 対象KW: 大学サッカー リーグ 種類（在庫表記「サッカー 大学リーグ 種類」）
- 記事slug: `daigaku-soccer-league-shurui-9chiku`

## KW差し替えの経緯

当初指示は「大学サッカー 強豪」だったが、`content/articles/daigaku-soccer-kyougou-daigaku.md`
（2026-09-15公開・タイトル「大学サッカー強豪はどこ？4地区リーグの優勝記録と2026年順位」）が
同一検索意図をすでにカバーしており、完全にカニバる。`docs/keyword-inventory.md` 2章（H）から
未着手の「サッカー 大学リーグ 種類」に差し替えた。

## SERP 1ページ目の顔ぶれ（WebSearch 2026-09-23）

| # | URL | 種別 |
| --- | --- | --- |
| 1 | https://www.jufa-kanto.jp/beginner/beginner1/ | 連盟公式（関東のみ） |
| 2 | https://hensachiterrace.com/trivia/13362 | 情報系メディア（403でfetch不可） |
| 3 | https://ja.wikipedia.org/wiki/関東大学サッカーリーグ戦 | Wikipedia |
| 4 | https://ja.wikipedia.org/wiki/東京都大学サッカーリーグ | Wikipedia |
| 5 | https://spaia.jp/column/soccer/2605 | スポーツメディア（関東のみ） |
| 6 | https://ab-soccer.club/blog/tokyotodaigakusoccerleague/ | 競技メディア（都県リーグ単体） |
| 7 | https://ab-soccer.club/blog/independence-league/ | 競技メディア（Iリーグ単体） |
| 8 | https://soccermama.jp/23405 | 保護者向けメディア |
| 9 | https://www.osakacitysc.com/magazine/233/ | 社会人リーグ主体（意図ずれ） |
| 10 | https://futsal-future.com/study_abroad/america_league/ | 米国大学リーグ（意図ずれ） |

## 共通点（検索意図の正解）

1. 「都道府県リーグ → 地区リーグ2部 → 地区リーグ1部 → 全国大会（インカレ）」というピラミッド構造の説明を求めている。
2. 具体的な所属校数・昇降格の枠数（関東は1部12・2部12・3部12の計36校、上下2チーム自動入替）を知りたい層が中心。
3. 「リーグの種類」には地区リーグ本体だけでなく、その下の都県リーグまで含めて説明することが期待されている。

## 上位陣に欠けている要素（差別化点）

1. **ほぼ全てが関東の話で完結している**。全日本大学サッカー連盟に9つの地域連盟が加盟しているという前提や、関西・東北・北信越の実構成に踏み込んだ記事がない。
2. **「同じ1部でもリーグの規模が違う」という定量比較がない**。本サイトの2026年シーズンデータでは関東1部・関西1部が12校、東北1部・北信越1部が8校と大きく異なる。
3. **現行シーズンの順位表という一次データへの導線がない**。制度説明で終わり、読者が「では今どうなっているか」を確認する先が示されていない。上位で唯一の一次情報である jufa-kanto の基礎知識ページも関東限定。

## この記事だけの要素（2つ）

- **A**: 2026年シーズンの4地区×1部/2部の所属校数比較表（関東12/12・関西12/12・東北8/13・北信越8/9）。サッカーマニアが各連盟公開情報から取得した `data/leagues/*/teams.json`（2026-09-22取得）に基づく。
- **B**: 所属校数の違いがシーズンの進み方に表れること。2026年9月22日時点の消化試合数が、関東1部11試合・関西1部12試合に対し東北1部7〜8試合・北信越1部7試合と差がある（`data/leagues/*/standings.json`）。

## 一次情報の出典

- 全日本大学サッカー連盟 組織図（9地域連盟）: https://www.jufa.jp/jufa/chart.html
- 関東大学サッカー連盟 はじめての大学サッカー: https://www.jufa-kanto.jp/beginner/beginner1/
- 関西学生サッカー連盟 関西学生リーグ2026: https://www.jufa-kansai.jp/taikai/2026-kansai/
- 東北サッカー協会 大学カテゴリ: https://tohoku-fa.jp/college/outline.html
- 北信越大学サッカー連盟: https://hufl.info/

## 注意（執筆時の制約）

- 東北1部の `standings.json` は得失点（gf/ga）が実態と整合しない値を含むため、**得失点・総得点は本文で使わない**（勝点・消化試合数・所属校数のみ使用）。
- 本サイト非対象の5地区（北海道・東海・中国・四国・九州）は「連盟が存在する」以上の詳細（部構成・校数）を書かない。
- Wikipedia・まとめメディアを出典にしない。
