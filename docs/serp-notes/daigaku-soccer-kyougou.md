# SERP分析メモ: 「大学サッカー 強豪」（2026-09-15）

- レーン: H（上位クエリ）／クエリ類型: Know（比較・一覧型、進学検討・観戦層が混在）
- 対象記事: `content/articles/daigaku-soccer-kyougou-daigaku.md`
- cta: sponsor

## 上位に出ていたURL（WebSearch 2026-09-15）

| # | URL | 媒体タイプ |
| --- | --- | --- |
| 1 | https://note.com/suzu_kii_to/n/n692114dc4c57 | note個人（関東限定の主観ランキング） |
| 2 | https://sposuru.com/contents/sports-quest/soccer-college-strong-team/ | スポーツ情報メディア |
| 3 | https://yoshikazunomori.com/spogei/1586 | スポーツ推薦ドットコム（進学情報） |
| 4 | https://tkufalcons.com/post-48/ | 大学スポーツランキングサイト |
| 5 | https://activel.jp/football/xdxeu | スポーツメディア（男女ランキング） |

WebFetchで内容確認したのは2（sposuru）と5（Activel）。

## 共通点と差別化点（3行）

1. **共通点**: いずれも「明治・法政・筑波・流経大・関学大・大体大」などの有名校を10校前後並べ、歴史的成績と有名OBを添える構成。読者は関東・関西の私大に偏った顔ぶれを見るだけで終わる。
2. **弱点**: sposuru は「関東1部10年で4回優勝」「早稲田27回優勝」等の数字を出すが**一次出典の明記がない**。Activel も成績を数値化しているが出典は画像のみ。さらに両者とも**東北・北信越の強豪に一切触れていない**（Activelは関東・関西のみと明記）。
3. **差別化**: 本サイトは(a)連盟公式・JFA公式の一次情報に出典を貼って優勝回数・歴代優勝校を示し、(b)関東/関西/東北/北信越の4地区すべてを扱い、(c)**2026年シーズンの進行中の順位表（自社データページ）**へ内部リンクして「今どうなっているか」まで見せる。競合はいずれも(c)を持たない。

## 使う一次情報（出典URL）

- 関東大学サッカーリーグ 1部優勝回数（早稲田27／筑波17／東京大・国士舘9／明治8／慶應7、注記「合計が102回になるのは、両校優勝が3回あるため」「筑波大学には、東京高等師範学校、東京教育大学も含む」）: https://www.jufa-kanto.jp/history/champions2/
- 関東1部 直近優勝校（2021流経大／2022明治／2023筑波／2024明治／2025筑波）: https://www.jufa-kanto.jp/history/champions/
- 関西学生サッカーリーグ1部 直近10年優勝校（2015関学／2016阪南／2017びわこ／2018〜2020大体大／2021・2022関学／2023京産／2024阪南／2025関学）: https://www.jufa-kansai.jp/pust_autumn/
- 全日本大学サッカー選手権（インカレ）歴代優勝: https://www.jfa.jp/match/alljapan_university_2023/history.html
- 第74回インカレ（2025年度）筑波大学が国士舘大に3-0で優勝、8大会ぶり10回目: https://www.tsukuba.ac.jp/news/20260105110141.html
- 総理大臣杯 歴代優勝（2021法政／2022国士舘／2023富士大／2024阪南／2025東洋）: https://www.jfa.jp/match/prime_minister_cup_2026/history.html
- 第50回総理大臣杯の開催期間2026/9/2〜9/12（※9/15時点でJFA公式に結果掲載なし＝記事では結果に触れない）: https://www.jfa.jp/match/prime_minister_cup_2026/
- 東北地区大学サッカーリーグ 1部は8チーム編成: https://tohoku-fa.jp/college/outline.html
- 2025年度 東北1部 優勝＝仙台大学（2位富士大／3位八戸学院大）: https://tohoku-fa.jp/?p=12265
- 第53回北信越大学サッカーリーグ1部 優勝＝新潟医療福祉大学（勝点39）: https://hufl.info/result/league53/

## 内部リンク（4リーグのstandings）

- https://soccermania.jp/kanto-1-2026/standings/index.html
- https://soccermania.jp/kansai-1-2026/standings/index.html
- https://soccermania.jp/tohoku-1-2026/standings/index.html
- https://soccermania.jp/hokushinetsu-1-2026/standings/index.html
- 補助: `kanto-2-2026/standings`（流通経済大学が2026年は2部2位＝「強豪でも2部にいる」ことの実データ）

## 注意点

- 関東・東北・北信越の順位表は編集部が試合結果から集計した参考値（README記載）。記事では「編集部集計の参考値」と明示する。
- 東北1部の東北学院大学の得失点データに異常値があるため、個別チームの得点data は引用しない。
- 第50回総理大臣杯（2026）の優勝校は未確認のため書かない。
