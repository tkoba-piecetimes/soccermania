# サッカーマニア — 大学サッカー情報メディア

大学サッカーの情報メディア「サッカーマニア」（運営: PieceTimes）。関東・関西・東北・北信越の
各連盟が公開している大学サッカーリーグの日程・結果ページから情報を取得し、静的サイトを
生成する。「ラグビーマニア」を雛形にした姉妹サイト。

- 公開URL: https://tkoba-piecetimes.github.io/soccermania/
- 対象（2026年シーズン）:
  - 関東（jufa-kanto.jp）: JR東日本カップ2026 第100回関東大学サッカーリーグ戦 1部・2部
  - 関西（jufa-kansai.jp）: 関西学生サッカーリーグ 1部・2部
  - 東北（jfa.jp 東北地区ページ）: 東北地区大学サッカーリーグ 1部・2部
  - 北信越（hufl.info）: 北信越大学サッカーリーグ 1部・2部
  - 詳細・robots.txt確認結果は `docs/soccer-sources.md` 参照

## 【重要】関東は football-system.jp を使用しない

関東の大学サッカーリーグは `football-system.jp` という外部システムに日程・結果ページが
委譲されている経路があり、この football-system.jp は **robots.txtで全クローラーを拒否**
している。本サイトはそちらには一切アクセスしない（iframe埋め込みの先も辿らない）。

その一方で、連盟公式サイト **jufa-kanto.jp 自身**が `/2026_league_report/` 配下に
節（第N節）ごとのマッチレポートページを自前HTMLで公開しており、そこに文章形式で
全試合の結果（チーム名・スコア・前半スコア）が掲載されている。jufa-kanto.jpの
robots.txtはクロール許可（`Allow: /`）のため、この節別レポートページのみを取得元とする
（`pipeline/fetch_kanto.py`）。節レポートに掲載されるのは**消化済み試合のみ**で、未消化
カードの将来日程は取得できない（節が公開され次第、日次Actionsで自動反映される）。

## 仕組み

```
jufa-kanto.jp（関東）/ jufa-kansai.jp（関西）/ jfa.jp東北地区（東北）/ hufl.info（北信越）
  → pipeline/fetch_kanto.py / fetch_kansai.py / fetch_tohoku.py / fetch_hokushinetsu.py
    ※ pipeline/common.py に共通ロジック（fetch/日付計算/順位集計）を集約
  → data/leagues/<region>-<部>-<年>/
  → pipeline/generate_site.py
  → site/
```

順位表は連盟によって扱いが異なる:
- **関西**: 連盟公式の順位表HTMLをそのまま採用（勝点・得失点差とも公式集計）
- **関東・東北・北信越**: 公式の順位表HTML（関東は画像でのみ公開）が取得できないため、
  試合結果から編集部が勝点3・分1・敗0、得失点差順で自前集計（参考値）

## 実行

```
python pipeline/fetch_all.py
python pipeline/generate_site.py
```

（地区ごとに個別実行したい場合は `pipeline/fetch_kanto.py` / `fetch_kansai.py` /
`fetch_tohoku.py` / `fetch_hokushinetsu.py` を単独で実行できる）

ローカル確認: `python -m http.server 8941 -d site`

## 未実装（今後）

- 過去シーズンのヒストリーデータ（`data/leagues/<code>/history/`）
- GA4 / Search Console 連携（`pipeline/generate_site.py` の `GA_MEASUREMENT_ID` /
  `GSC_VERIFICATION` は現在未設定）
- 読みもの記事・用語辞典（`content/articles/`, `content/glossary.json` を追加すれば
  自動で有効化される）
- 関東: 1節が2日に分割される場合の個別試合日付は本文の試合数表記から推定しており、
  推定できないケースは日付nullで保存される（`pipeline/fetch_kanto.py`のdocstring参照）
