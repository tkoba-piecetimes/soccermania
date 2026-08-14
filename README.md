# サッカーマニア — 大学サッカー情報メディア

大学サッカーの情報メディア「サッカーマニア」（運営: PieceTimes）。関西・東北・北信越の
各連盟が公開している大学サッカーリーグの日程・結果ページから情報を取得し、静的サイトを
生成する。「ラグビーマニア」を雛形にした姉妹サイト。

- 公開URL: https://tkoba-piecetimes.github.io/soccermania/
- 対象（2026年シーズン）:
  - 関西（jufa-kansai.jp）: 関西学生サッカーリーグ 1部・2部
  - 東北（jfa.jp 東北地区ページ）: 東北地区大学サッカーリーグ 1部・2部
  - 北信越（hufl.info）: 北信越大学サッカーリーグ 1部・2部
  - 関東は対象外（保留）。理由は下記参照
  - 詳細・除外理由・robots.txt確認結果は `docs/soccer-sources.md` 参照

## 【重要】関東が対象外の理由

関東の大学サッカーリーグは `football-system.jp` という外部システムに結果ページが
委譲されており、この football-system.jp が **robots.txtで全クローラーを拒否**している。
JUFA関東公式サイト (`jufa-kanto.jp`) の日程・結果ページも中身は football-system.jp への
埋め込みのため同様に対象外。代替ソースを15分調査したが、公式（連盟）データとして
使えるものが見つからなかったため、関東は保留とした（詳細: `docs/soccer-sources.md`）。

## 仕組み

```
jufa-kansai.jp（関西）/ jfa.jp東北地区（東北）/ hufl.info（北信越）
  → pipeline/fetch_kansai.py / fetch_tohoku.py / fetch_hokushinetsu.py
    ※ pipeline/common.py に共通ロジック（fetch/日付計算/順位集計）を集約
  → data/leagues/<region>-<部>-<年>/
  → pipeline/generate_site.py
  → site/
```

順位表は連盟によって扱いが異なる:
- **関西**: 連盟公式の順位表HTMLをそのまま採用（勝点・得失点差とも公式集計）
- **東北・北信越**: 公式の順位表が公開されていないため、試合結果から編集部が
  勝点3・分1・敗0、得失点差順で自前集計（参考値）

## 実行

```
python pipeline/fetch_all.py
python pipeline/generate_site.py
```

（地区ごとに個別実行したい場合は `pipeline/fetch_kansai.py` / `fetch_tohoku.py` /
`fetch_hokushinetsu.py` を単独で実行できる）

ローカル確認: `python -m http.server 8941 -d site`

## 未実装（今後）

- 関東の代替データソースが見つかり次第、対象に追加
- 過去シーズンのヒストリーデータ（`data/leagues/<code>/history/`）
- GA4 / Search Console 連携（`pipeline/generate_site.py` の `GA_MEASUREMENT_ID` /
  `GSC_VERIFICATION` は現在未設定）
- 読みもの記事・用語辞典（`content/articles/`, `content/glossary.json` を追加すれば
  自動で有効化される）
