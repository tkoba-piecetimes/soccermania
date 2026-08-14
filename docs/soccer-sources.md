# データソース調査記録（サッカー）

大学サッカーは地区ごとに連盟が分かれており、ラグビー版のような「3地区で全国カバー」は
成立しない（関東・関西・東北・北信越・東海・中国・四国・九州など地区数が多い）。
今回は**関西・東北・北信越**の3地区を対象とする（2026-08-14時点の調査）。

## 【最重要】football-system.jp は使用禁止

関東・九州・中国など複数地区の大学リーグが `football-system.jp` という共通の外部システム
（NTTデータ系の大会運営プラットフォーム）に結果ページを委譲しており、この
football-system.jp が **robots.txtで全クローラーを拒否**している。よって以下は対象外：

- **関東**: JUFA関東公式サイト (`jufa-kanto.jp`) の日程・結果ページ
  (`league_data.php?keyno=1&ctg=1` → `/league/#league`) は一見自前ページに見えるが、
  中身は `football-system.jp/fss/pub_taikaigamelist.php?lid=...` 等への埋め込み
  （iframe/fetch）で、実データはfootball-system.jp側にある。確認済みで**対象外・保留**。
- 上記以外にも中国・四国等が同システムを使っている可能性があるが未調査（対象外方針のため
  調査不要と判断）。

## 関東の代替ソース調査（2026-08-14・15分間）

jfa.jpのmatch center（東北で使われている `match_47fa/` 系のURL）に関東地方大学サッカーの
ページがあるか確認したが `match_47fa/103_kanto/...` は404。関東は複数県にまたがり
プレフェクチャー単位のFAでは大学リーグを扱っていないため、jfa.jpのmatch centerには
関東大学リーグの窓口がない。

第三者メディア（ゲキサカ: `web.gekisaka.jp/competition/...`）に日程・結果・順位表が
掲載されているのを発見したが、(1) 連盟公式ではなく商用ニュースメディアであり
「各連盟名+リンク」という出典方針にそぐわない、(2) 利用規約・robots.txtが未確認、
という理由で今回は採用を見送った。東京都大学サッカー連盟 (`f-togakuren.com`) も
発見したが、これは関東の一部（東京都）のみを扱う下部組織であり関東大学リーグ全体の
代替にはならない。

**結論: 関東は保留。football-system.jp を経由しない公式データが見つかれば将来追加する。**

## 関西学生サッカー連盟 (jufa-kansai.jp)

- 順位表: `https://www.jufa-kansai.jp/meet/student/{yy}data/team_rank_{部}.html`
  （`{部}` は1=1部、2=2部。**Shift_JIS配信**。連盟が算出した公式の勝点・得失点差が
  そのまま掲載されているため、東北・北信越と違いこちらを正として採用）
- 日程・結果: `https://www.jufa-kansai.jp/meet/student/{yy}data/nittei_{部}_{半期}.html`
  （`{半期}` は1=前期、2=後期。後期開幕前は404を返すため、取得できたものだけを使う実装
  にしてある）
- 表はHTML4時代の`<font>`+`<td class="matrix_...">`構成。日付セルに
  「4/29（水）祝」のような祝日注記が付くことがあり、`[^<]*<br>`で緩く受けるようにした
  （当初、祝日注記付きの日付だけ正規表現が外れて12試合欠落するバグがあり修正済み）
- 対象: **1部・2部のみ**（3部は連盟サイト上に存在するが今回は対象外。指示範囲外のため）
- 実装: `pipeline/fetch_kansai.py`

## 東北サッカー協会 (jfa.jp内 東北地区ページ)

- 日程・結果: `https://www.jfa.jp/match_47fa/102_tohoku/{year}_university/div{N}/thfa/schedule.html`
  （`{N}`は1=1部、2=2部。3部相当のURLは404で存在しない）
- `robots.txt`確認済み（`https://www.jfa.jp/robots.txt`）: MJ12botとApplebot
  （`/nadeshikohiroba/`のみ）を拒否しているだけで、`match_47fa/`配下は制限なし。
  クロール可能と判断
- 表は`class="table_jfa-match-center"`。不戦勝（棄権）の試合はスコアセルに
  「N (棄権) M」の形式で入り、日程が「未定」のまま結果だけ確定していることがある
  （この場合 `date: null` のまま `status: "played"` として保存する）
- 公式の順位表ページは公開されていないため、`common.compute_standings`
  （勝点3・分1・敗0、得失点差順）で自前集計する
- 実装: `pipeline/fetch_tohoku.py`

## 北信越大学サッカー連盟 (hufl.info)

- 日程・結果: `https://hufl.info/league/schedule-div{N}/`（`{N}`は1=1部、2=2部）。
  WordPressサイトで、1ページ内に前期・後期それぞれの`<table>`が並ぶ
- `robots.txt`確認済み: `/wp-admin/`のみ拒否。対象パスは制限なし
- 未消化の試合はスコアセルが`&#8211;`（enダッシュ実体参照）のみになる。日付の区切り文字が
  まれに全角セミコロン「10;00」になっている箇所があり、`[:;：]`で許容する実装にした
- 公式の順位表ページは公開されていないため、`common.compute_standings`で自前集計する
- 実装: `pipeline/fetch_hokushinetsu.py`

## リーグID設計

`{地域}-{部}-{年}` 形式（例: `kansai-1-2026`）。ラグビー版の`kansai-a`のような部を
アルファベットで表す方式ではなく、大学サッカーの「1部・2部」呼称にそのまま合わせた。
