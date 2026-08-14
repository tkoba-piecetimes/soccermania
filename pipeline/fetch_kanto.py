# -*- coding: utf-8 -*-
"""関東大学サッカー連盟公式サイト（jufa-kanto.jp）から大学サッカーの日程・結果を取得し、
data/leagues/<code>/ に正規化JSONとして保存する。

データ出典: 関東大学サッカー連盟 (https://www.jufa-kanto.jp/)
対象: JR東日本カップ2026 第100回関東大学サッカーリーグ戦 1部・2部（3部以下は対象外）。

【重要】football-system.jp は使用しない
関東の結果配信は football-system.jp という外部システム（robots.txtで全クローラー拒否）に
委譲されている経路があるが、本スクリプトはそちらには一切アクセスしない（iframe埋め込みの
先も辿らない）。使用するのは連盟公式サイト自身が /{年}_league_report/ 配下に自前HTMLで
公開している「節別マッチレポート」ページのみ。jufa-kanto.jpのrobots.txtは
`User-agent: * / Allow: /` でクロール許可されていることを確認済み。

節の一覧は `/{年}_league_report/` のインデックスページ（サイドバーのツリーメニュー）内の
リンクを列挙して取得する（sec_NN〜sec_30等への総当たりは行わない）。通常節 sec_NN と、
延期分の消化試合をまとめた sec_NNex の両方が存在する。

各節ページ本文の「全試合結果と得点者」見出し以降に
  チームA　◯(前半◯-◯)◯　チームB<br />　得点者)...
の形式で試合結果が列挙されている（得点者情報は本パイプラインのデータモデルでは扱わない
ため破棄する）。得失点差の計算に必要なスコアと日付のみを抽出する。

【書式ゆれ】
- チーム名: 通常「○○大学」だが「桐蔭横浜大」のように「大学」が「大」に省略される回が
  まれにあり、そのままだと同一チームが別チーム扱いになり順位集計が壊れる。
  `normalize_team_name` で「大学」で終わらない「大」終わりの名前は「学」を補って統一する。
  また1部第8節レポートには「駒澤学大」という誤字（「学」「大」の順序が入れ替わっている）
  があり、これは汎用ルールでは救えないため `TEAM_NAME_ALIASES` に個別登録している。
- 得点者見出し: 「得点者)」（半角丸カッコ）と「得点者）」（全角丸カッコ）が混在する。
  スコア抽出では見出しより前の文字列だけを使うため実害はない。
- 開催日: 通常節は本文冒頭〜レポート本文の紹介文に開催日が書かれているが、書き方の
  ゆれが大きい。「5月9日(土)に全6試合が行われた」（1日・全試合共通）だけでなく、
  「5月16日(土)に4試合、17日(日)に2試合が行われた」（1節が2日に分割）、
  「4月11日(土)に行われた4試合のうち」（語順が逆）、「翌5日には4試合が行われた」
  （月省略・相対表記）、「4月4日(土)に開幕した」（試合数の言及なし）などが混在する。
  さらに次節の予告文（例:「次節は5月9日(土)に全6試合が行われる」＝未来形）が同じ節の
  本文中に登場することがあり、日付だけを機械的に拾うと次節の日付を誤って混入してしまう。
  そのため「行われた」「開幕した」を含む文（＝過去形＝実際に消化された試合の告知）だけを
  対象に日付と試合数を抽出し、「行われる」（未来形）の文は無視する
  （`extract_date_counts` 参照）。1節に複数日付が見つかり、かつ各日付の試合数の合計が
  その節の試合数と一致する場合のみ、試合結果一覧の並び順（=速報が届いた順）に沿って
  日付ごとに按分する（この場合 note に按分である旨を残す）。試合数が数え合わず日付を
  一意に決められない場合は日付を `null` にする（スコアは正しく取得できる。note欄に理由）。
  延期分ページ（sec_NNex）は `<p><strong>■7月11日(土)</strong></p>` の形式で試合結果の
  直前に日付見出しが入ることが多く、これがある場合はそちらを優先して個別に日付を割り当てる
  （延期分ページでも1試合のみで見出しがないパターンがあり、その場合は上記の紹介文方式で
  代替する）。
- 会場: 節レポートには試合ごとの会場情報が掲載されていないため "非公開" とする。

順位表は連盟サイト上では画像（JPEG）としてのみ公開されており構造化データが取れないため、
common.compute_standings で試合結果から自前集計する（勝点3・分1・敗0、得失点差順）。

このレポートに掲載されるのは消化済み試合のみ。未消化カードの将来日程は掲載されないため、
本スクリプトも将来日程の先取りはしない（節が公開され次第、日次Actionsで自動反映される）。
"""
import html as html_lib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from common import fetch, compute_standings, build_teams
from team_slugs import slug_for

BASE = "https://www.jufa-kanto.jp"
CURRENT_SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"
REPORT_INDEX = f"{BASE}/{CURRENT_SEASON}_league_report/"

# (部) -> (リーグコード, 表示名)
DIVISIONS = {
    1: ("kanto-1-2026", "JR東日本カップ2026 第100回関東大学サッカーリーグ戦1部"),
    2: ("kanto-2-2026", "JR東日本カップ2026 第100回関東大学サッカーリーグ戦2部"),
}

SEC_LINK_RE = re.compile(
    r'href="(/' + str(CURRENT_SEASON) + r'_league_report/div([12])/sec_[0-9a-z]+)/"')
SECTION_RE = re.compile(r"全試合結果と得点者(.*?)<style", re.DOTALL)
P_RE = re.compile(r"<p>(.*?)</p>", re.DOTALL)
BR_RE = re.compile(r"<br\s*/?>")
DATE_HEADER_RE = re.compile(r"<strong>■(\d{1,2})月(\d{1,2})日")
MATCH_RE = re.compile(
    r"^\s*(?P<home>.+?)\s*(?P<hs>\d+)\((?P<h1>\d+)-(?P<h2>\d+)\)(?P<as_>\d+)\s*(?P<away>.+?)\s*$")

# 「N月N日(土)」「N日(日)」（月省略、直前の月を継承）の日付そのものを検出する
# （試合数の有無は問わない。1節1日付だけの節ならこれだけで確定できる）。
DATE_ONLY_RE = re.compile(r"(?:(\d{1,2})月)?(\d{1,2})日(?:[\(（][^)）]{1,6}[\)）])?")
# 「N月N日(土)に…M試合」「N月N日(土)に行われたM試合」を語順ゆれ込みで拾う
# （間の助詞・"行われた"・"全"・大会正式名称の挿入等、最大18文字までの揺れを許容）。
DATE_COUNT_RE = re.compile(
    r"(?:(\d{1,2})月)?(\d{1,2})日(?:[\(（][^)）]{1,6}[\)）])?.{0,18}?(\d+)試合")

MULTI_DATE_NOTE = "日程未定（節内に複数の開催日があり個別試合日を特定できず。詳細は連盟サイト参照）"
SPLIT_DATE_NOTE = "開催日は本文の試合数表記から推定（節内に複数の開催日あり）"


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return html_lib.unescape(s)


# 個別の誤字・表記ゆれ（自動補正ルールでは救えないもの）。
# 「駒澤学大」は1部第8節レポートの誤字（正しくは「駒澤大学」。「学」「大」の順序が
# 入れ替わっている）。汎用ルールで「学」を補うと「駒澤学大学」になってしまうため
# 個別に登録する。
TEAM_NAME_ALIASES = {
    "駒澤学大": "駒澤大学",
}


def normalize_team_name(name: str) -> str:
    """「桐蔭横浜大」のような「大学」の省略表記を「桐蔭横浜大学」に統一する。
    これをしないと同一チームが表記ゆれで2チーム扱いになり順位集計が壊れる。"""
    name = name.strip()
    if name in TEAM_NAME_ALIASES:
        return TEAM_NAME_ALIASES[name]
    if name.endswith("大") and not name.endswith("大学"):
        name = name + "学"
    return name


def season_date_iso(month: int, day: int, year: int = CURRENT_SEASON) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def list_section_urls(div: int) -> list[str]:
    html = fetch(REPORT_INDEX)
    urls = []
    for path, d in SEC_LINK_RE.findall(html):
        if int(d) == div:
            urls.append(BASE + path + "/")
    return list(dict.fromkeys(urls))  # 出現順を保ったまま重複除去


def extract_date_counts(intro_html: str, n_matches: int) -> tuple[list[tuple[int, int]], list[int] | None]:
    """節ページ冒頭〜レポート本文（「全試合結果と得点者」より前）から、実際に消化された
    試合の開催日を抽出する。「行われた/行われ、/開幕した」を含む文（過去形・過去の出来事の
    説明）だけを対象にし、次節の予告文（「…に行われる」＝未来形）は否定先読みで除外する。

    戻り値: (出現順の日付リスト, 日付ごとの試合数リスト)。
    日付は「N月N日」の言及があれば試合数の有無に関わらず検出する（1節1日付の節は
    これだけで確定できる）。1節に複数日付がある場合は、さらに「N日にM試合」の形で
    試合数まで確認でき、かつ合計がn_matchesと一致した場合のみ試合数リストを返す
    （一致しなければNoneとし、呼び出し側はdate=nullにフォールバックする）。"""
    plain = strip_tags(intro_html).replace("　", " ")
    order: list[tuple[int, int]] = []
    counts: dict[tuple[int, int], int] = {}
    last_month = None
    for sentence in re.split("。", plain):
        if not re.search(r"行われ(?!る)|開幕した", sentence):
            continue  # 未来形（次節予告）などは対象外
        for m in DATE_ONLY_RE.finditer(sentence):
            month = int(m.group(1)) if m.group(1) else last_month
            if month is None:
                continue
            last_month = month
            key = (month, int(m.group(2)))
            if key not in order:
                order.append(key)
        for m in DATE_COUNT_RE.finditer(sentence):
            month = int(m.group(1)) if m.group(1) else last_month
            if month is None:
                continue
            key = (month, int(m.group(2)))
            counts[key] = int(m.group(3))
    if not order:
        return [], None
    if len(counts) == len(order) and sum(counts.values()) == n_matches:
        return order, [counts[k] for k in order]
    return order, None


def parse_section(html: str, category_label: str, url: str) -> list[dict]:
    sec_m = SECTION_RE.search(html)
    if not sec_m:
        print(f"[warn] 「全試合結果と得点者」セクションが見つからない: {url}", file=sys.stderr)
        return []
    section_html = sec_m.group(1)
    intro_html = html[: sec_m.start()]
    has_headers = bool(DATE_HEADER_RE.search(section_html))

    # 1st pass: 見出し（■日付）と試合行を出現順に集める（日付割り当てはまだしない）
    raw: list[tuple[str, object]] = []
    for p_html in P_RE.findall(section_html):
        dm = DATE_HEADER_RE.search(p_html)
        if dm:
            raw.append(("header", (int(dm.group(1)), int(dm.group(2)))))
            continue
        text = BR_RE.sub("\n", p_html)
        line = strip_tags(text.split("得点者", 1)[0])
        line = line.replace("　", " ").strip()
        if not line:
            continue
        mm = MATCH_RE.match(line)
        if not mm:
            print(f"[warn] パース失敗（書式ゆれの可能性）: {url} : {line!r}", file=sys.stderr)
            continue
        home = normalize_team_name(mm.group("home"))
        away = normalize_team_name(mm.group("away"))
        if not home or not away:
            continue
        raw.append(("match", (home, away, int(mm.group("hs")), int(mm.group("as_")))))

    match_payloads = [p for k, p in raw if k == "match"]
    n_matches = len(match_payloads)

    # 2nd pass: 各試合に日付・note を割り当てる
    if has_headers:
        dated: list[tuple[str | None, tuple, str]] = []
        current_date = None
        for kind, payload in raw:
            if kind == "header":
                current_date = season_date_iso(*payload)
            else:
                dated.append((current_date, payload, ""))
    else:
        dates, counts = extract_date_counts(intro_html, n_matches)
        if len(dates) == 1:
            d_iso = season_date_iso(*dates[0])
            dated = [(d_iso, p, "") for p in match_payloads]
        elif len(dates) >= 2 and counts is not None:
            print(f"[info] 節内2日程を試合数表記から按分: {url} "
                  f"{list(zip(dates, counts))}", file=sys.stderr)
            dated = []
            idx = 0
            for (month, day), c in zip(dates, counts):
                d_iso = season_date_iso(month, day)
                for _ in range(c):
                    dated.append((d_iso, match_payloads[idx], SPLIT_DATE_NOTE))
                    idx += 1
        else:
            if dates:
                print(f"[warn] 1節に複数日程が混在し試合数が数え合わない"
                      f"（個別試合日を特定できずdate=nullにします）: {url} dates={dates}",
                      file=sys.stderr)
            else:
                print(f"[warn] 開催日を紹介文から抽出できず（date=nullにします）: {url}",
                      file=sys.stderr)
            dated = [(None, p, MULTI_DATE_NOTE) for p in match_payloads]

    matches = []
    for d_iso, (home, away, hs, as_), note in dated:
        matches.append({
            "id": f"{d_iso or 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
            "date": d_iso,
            "time": "未定",
            "category": category_label,
            "home": home,
            "away": away,
            "home_slug": slug_for(home),
            "away_slug": slug_for(away),
            "venue": "非公開",
            "status": "played",
            "home_score": hs,
            "away_score": as_,
            "note": note,
        })
    return matches


def fetch_division(div: int, label: str) -> dict | None:
    try:
        urls = list_section_urls(div)
    except Exception as e:
        print(f"  {label}: 節一覧の取得失敗（{e}）")
        return None
    if not urls:
        print(f"  {label}: インデックスページに節へのリンクが見つからない")
        return None
    matches: list[dict] = []
    for url in urls:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"  {label}: {url} 取得失敗（{e}）")
            continue
        ms = parse_section(html, label, url)
        matches.extend(ms)
        sec_name = url.rstrip("/").rsplit("/", 1)[-1]
        print(f"  {label} {sec_name}: 試合{len(ms)}件")
    return {
        "matches": matches,
        "standings": compute_standings(matches, slug_for),
        "teams": build_teams(matches, slug_for),
        "label": label,
    }


def main() -> None:
    ok = 0
    for div, (code, label) in DIVISIONS.items():
        print(f"-- {label} ({code}) --")
        d = fetch_division(div, label)
        if d is None or not d["matches"]:
            print(f"{code}: データなし（取得失敗の可能性）")
            continue
        out_dir = DATA_DIR / code
        out_dir.mkdir(parents=True, exist_ok=True)
        played = sum(1 for m in d["matches"] if m["status"] == "played")
        meta = {
            "code": code,
            "region": "関東",
            "gender": "男子",
            "group": "関東大学サッカーリーグ",
            "league": label,
            "season_year": CURRENT_SEASON,
            "source": "関東大学サッカー連盟",
            "source_url": REPORT_INDEX,
            "source_updated_at": date.today().isoformat(),
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
        }
        (out_dir / "matches.json").write_text(
            json.dumps(d["matches"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "standings.json").write_text(
            json.dumps(d["standings"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "teams.json").write_text(
            json.dumps(d["teams"], ensure_ascii=False, indent=1), encoding="utf-8")
        (out_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{code}: {label} 試合{len(d['matches'])}件(結果{played}) チーム{len(d['teams'])}")
        ok += 1
    print(f"done: {ok}/{len(DIVISIONS)} divisions")


if __name__ == "__main__":
    main()
