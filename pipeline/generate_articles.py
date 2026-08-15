# -*- coding: utf-8 -*-
"""data/leagues/ の試合結果から「節レビュー記事」を自動生成し、content/articles/ に
Markdown（generate_site.pyのload_articles()が読める平文frontmatter形式）として書き出す
（Type A: テンプレート生成・LLM不使用）。

生成単位:
  - 関東（1部・2部）: 節（sec_NN）。matches.json には節番号そのものは保存されていないため、
    試合の並び順（= 連盟サイトの節別レポートページを取得順に並べた順序。fetch_kanto.py参照）
    と開催日の近さから節の区切りを推定し、出現順に第1節・第2節…と連番を振る。
    節内に複数開催日がある場合や、開催日が未確定（date=null。関東1部第1節など）の場合も
    1つの節として扱う（エラーにはしない。日付未確定の節は代表日を近傍の節から推定する）。
  - 関西・東北・北信越: 節番号の概念がデータに存在しないため、開催日が近い試合同士を
    「試合日クラスタ」（週末単位）としてまとめる。date=null の試合（不戦勝など）は
    どの週末に属するか判定できないためクラスタ化の対象から除外する（エラーにはしない）。

slug:
  - 関東: review-<league>-sec<NN>（<league>は年サフィックスを除いたリーグコード。例: kanto-1）
  - その他: review-<league>-<YYYYMMDD>（クラスタの代表日）
既存のslug（content/articles/<slug>.md が既に存在する）はスキップする。

1回の実行につき最大2記事まで生成する（全リーグを横断し、代表日が古いクラスタから優先）。
まだ試合が続いているリーグ（scheduled試合が残っている）では、直近のクラスタは今後の
試合追加でまだ変わる可能性があるため、候補から除外する（シーズン終了済みのリーグは対象外
にしない）。

このスクリプトは pipeline/generate_site.py の直前（.github/workflows/update.yml内）に
実行する。generate_site.py 側の変更は不要（load_articles/build_articles は既存の仕組み
をそのまま使う）。
"""
import json
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "leagues"
CONTENT_DIR = ROOT / "content" / "articles"

MAX_ARTICLES_PER_RUN = 2

# 節/クラスタの区切り判定に使う日付ギャップの閾値（日）。閾値以下なら同じ節/クラスタ、
# 超えたら次の節/クラスタとみなす。同一節内の開催日（土・日など）は差1日程度、
# 次の節までは通常6〜7日以上空くため、この値で概ね正しく分割できる（検証済み）。
ROUND_GAP_DAYS = 2
WEEKEND_GAP_DAYS = 2

WEEKDAYS_JP = ["月", "火", "水", "木", "金", "土", "日"]

CATEGORY = "結果まとめ"


# ---------------------------------------------------------------- data loading

def load_league(code: str) -> dict | None:
    d = DATA_DIR / code
    if not (d / "matches.json").exists():
        return None
    return {
        "code": code,
        "matches": json.loads((d / "matches.json").read_text(encoding="utf-8")),
        "standings": json.loads((d / "standings.json").read_text(encoding="utf-8")),
        "meta": json.loads((d / "meta.json").read_text(encoding="utf-8")),
    }


def short_code(code: str) -> str:
    """'kanto-1-2026' -> 'kanto-1'（年サフィックスを除去）。"""
    parts = code.rsplit("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return code


def existing_slugs() -> set[str]:
    if not CONTENT_DIR.exists():
        return set()
    return {f.stem for f in CONTENT_DIR.glob("*.md")}


# ---------------------------------------------------------------- clustering

def cluster_by_round(matches: list[dict]) -> list[list[dict]]:
    """関東用: 元の並び順（節の取得順）を保ったまま、開催日の近さで節を区切る。
    date=null の試合が連続する区間は1つの節としてまとめる。"""
    played = [m for m in matches if m["status"] == "played" and m.get("home_score") is not None]
    clusters: list[list[dict]] = []
    cur: list[dict] = []
    cur_last_date: str | None = None
    cur_has_null = False
    for m in played:
        d = m["date"]
        if not cur:
            cur = [m]
            cur_last_date = d
            cur_has_null = d is None
            continue
        same = False
        if d is None and cur_has_null:
            same = True
        elif d is not None and cur_last_date is not None:
            gap = (date.fromisoformat(d) - date.fromisoformat(cur_last_date)).days
            if 0 <= gap <= ROUND_GAP_DAYS:
                same = True
        if same:
            cur.append(m)
            if d is not None:
                cur_last_date = d
        else:
            clusters.append(cur)
            cur = [m]
            cur_last_date = d
            cur_has_null = d is None
    if cur:
        clusters.append(cur)
    return clusters


def cluster_by_weekend(matches: list[dict]) -> tuple[list[list[dict]], int]:
    """関東以外用: 開催日が確定している試合だけを日付順に並べ、近い日付同士を
    1つの試合日クラスタ（週末単位）にまとめる。date=null の試合（不戦勝等でどの
    週末に属するか判定できないもの）は対象から除外する（件数のみ返す）。"""
    played = [m for m in matches if m["status"] == "played" and m.get("home_score") is not None]
    dated = sorted((m for m in played if m["date"]), key=lambda m: m["date"])
    undated_count = sum(1 for m in played if not m["date"])
    clusters: list[list[dict]] = []
    cur: list[dict] = []
    cur_last: str | None = None
    for m in dated:
        d = m["date"]
        if not cur:
            cur = [m]
            cur_last = d
            continue
        gap = (date.fromisoformat(d) - date.fromisoformat(cur_last)).days
        if gap <= WEEKEND_GAP_DAYS:
            cur.append(m)
            cur_last = d
        else:
            clusters.append(cur)
            cur = [m]
            cur_last = d
    if cur:
        clusters.append(cur)
    return clusters, undated_count


# ---------------------------------------------------------------- text helpers

def date_jp(iso: str) -> str:
    d = date.fromisoformat(iso)
    wd = WEEKDAYS_JP[d.weekday()]
    return f"{d.month}月{d.day}日（{wd}）"


def date_range_label(dates: list[str]) -> str:
    uniq = sorted(set(dates))
    start = date.fromisoformat(uniq[0])
    end = date.fromisoformat(uniq[-1])
    if start == end:
        return f"{start.month}月{start.day}日"
    if start.month == end.month:
        return f"{start.month}月{start.day}日～{end.day}日"
    return f"{start.month}月{start.day}日～{end.month}月{end.day}日"


def team_link(name: str, slug: str, league_code: str) -> str:
    # articles/<slug>/index.html から見た相対パス（サイトルートへ2階層上がる）。
    return f"[{name}](../../{league_code}/clubs/{slug}/index.html)"


def results_table(matches: list[dict], league_code: str, date_confirmed: bool) -> str:
    rows = ["| 日付 | 対戦 | スコア |", "| --- | --- | --- |"]
    for m in matches:
        d = date_jp(m["date"]) if (date_confirmed and m["date"]) else "日付未定"
        home = team_link(m["home"], m["home_slug"], league_code)
        away = team_link(m["away"], m["away_slug"], league_code)
        rows.append(f'| {d} | {home} vs {away} | {m["home_score"]} - {m["away_score"]} |')
    return "\n".join(rows)


def standings_table(entries: list[dict], league_code: str, limit: int | None = None) -> str:
    rows = ["| 順位 | チーム | 勝点 | 得失点差 |", "| --- | --- | --- | --- |"]
    for e in entries[:limit] if limit else entries:
        team = team_link(e["team"], e["slug"], league_code)
        rows.append(f'| {e["rank"]} | {team} | {e["points"]} | {e["goal_diff"]} |')
    return "\n".join(rows)


def source_line(meta: dict) -> str:
    if meta["region"] == "関東":
        # football-system.jp には触れず、連盟公式サイトのトップURLを出典として明記する。
        return "- [関東大学サッカー連盟](https://www.jufa-kanto.jp/)"
    return f'- [{meta["source"]}]({meta["source_url"]})'


# ---------------------------------------------------------------- candidate building

def build_candidate(league: dict, cluster: list[dict], round_no: int | None,
                     next_cluster: list[dict] | None) -> dict:
    meta = league["meta"]
    code = league["code"]
    sc = short_code(code)
    league_name = meta["league"]
    dates = [m["date"] for m in cluster if m["date"]]
    date_confirmed = bool(dates)

    if round_no is not None:
        slug = f"review-{sc}-sec{round_no:02d}"
        round_label = f"第{round_no}節"
    else:
        rep = date_range_label(dates)
        slug = f"review-{sc}-{dates[0].replace('-', '')}"
        round_label = rep

    if date_confirmed:
        repr_date = min(dates)
    elif next_cluster:
        nd = sorted(m["date"] for m in next_cluster if m["date"])
        if nd:
            repr_date = (date.fromisoformat(nd[0]) - timedelta(days=7)).isoformat()
        else:
            repr_date = meta["fetched_at"][:10]
    else:
        repr_date = meta["fetched_at"][:10]

    entries = league["standings"].get("総合", [])
    leader = entries[0] if entries else None

    n = len(cluster)
    lead = f"{league_name}の{round_label}、全{n}試合の結果をまとめました。"
    if leader:
        lead += f"現在の首位は{leader['team']}（勝点{leader['points']}、得失点差{leader['goal_diff']}）です。"
    if not date_confirmed:
        lead += "なお、この節は連盟公式サイト上で個別の試合日が確定していないため、開催日は掲載順からの推定です。詳細は出典元をご確認ください。"

    body_parts = [lead, "", "## 試合結果", "",
                  results_table(cluster, code, date_confirmed), "",
                  "## 順位表（勝点・得失点差）", "",
                  standings_table(entries, code), "",
                  "## 出典", "", source_line(meta)]
    body = "\n".join(body_parts)

    title = f"【{league_name}】{round_label}の結果まとめ"
    description = f"{league_name}{round_label}の試合結果と最新の順位表（勝点・得失点差）をまとめました。"

    return {
        "slug": slug,
        "sort_date": repr_date,
        "title": title,
        "description": description,
        "category": CATEGORY,
        "date": repr_date,
        "body": body,
    }


def league_candidates(league: dict) -> list[dict]:
    meta = league["meta"]
    matches = league["matches"]
    scheduled_remaining = any(m["status"] == "scheduled" for m in matches)
    candidates = []

    if meta["region"] == "関東":
        clusters = cluster_by_round(matches)
        if scheduled_remaining and clusters:
            # 実際にはscheduled=0（関東は現状全試合played）のケースが大半だが、
            # 将来シーズンで日程が残っている場合に備えたガード。
            clusters = clusters[:-1]
        for i, c in enumerate(clusters, 1):
            nxt = clusters[i] if i < len(clusters) else None
            candidates.append(build_candidate(league, c, i, nxt))
    else:
        clusters, undated_count = cluster_by_weekend(matches)
        if undated_count:
            print(f"  [info] {league['code']}: 開催日未確定の試合{undated_count}件は"
                  f"週末クラスタの対象外としてスキップ（エラーにはしない）")
        if scheduled_remaining and clusters:
            clusters = clusters[:-1]
        for c in clusters:
            candidates.append(build_candidate(league, c, None, None))

    return candidates


# ---------------------------------------------------------------- write

FRONTMATTER_TMPL = """---
title: {title}
description: {description}
category: {category}
date: {date}
cta: sponsor
---

{body}
"""


def write_article(c: dict) -> None:
    # cta: sponsor固定（部活メディア→ツナカレ接続設計 D3。節レビュー記事は
    # 読者がファン・OB中心のため「この部活・競技を応援したい方へ」CTA帯を表示する）。
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    text = FRONTMATTER_TMPL.format(
        title=c["title"], description=c["description"],
        category=c["category"], date=c["date"], body=c["body"])
    (CONTENT_DIR / f'{c["slug"]}.md').write_text(text, encoding="utf-8")


def main() -> None:
    league_codes = sorted(p.name for p in DATA_DIR.iterdir() if p.is_dir()) if DATA_DIR.exists() else []
    leagues = [lg for lg in (load_league(code) for code in league_codes) if lg is not None]
    if not leagues:
        print("[generate_articles] リーグデータがありません（先にfetch_all.pyを実行）。スキップします。")
        return

    existing = existing_slugs()
    all_candidates = []
    for lg in leagues:
        for c in league_candidates(lg):
            if c["slug"] in existing:
                continue
            all_candidates.append(c)

    all_candidates.sort(key=lambda c: (c["sort_date"], c["slug"]))

    to_write = all_candidates[:MAX_ARTICLES_PER_RUN]
    for c in to_write:
        write_article(c)
        print(f'[生成] {c["slug"]}: {c["title"]}')

    remaining = len(all_candidates) - len(to_write)
    print(f"[generate_articles] 生成{len(to_write)}件 / 未生成ストック{remaining}件")


if __name__ == "__main__":
    main()
