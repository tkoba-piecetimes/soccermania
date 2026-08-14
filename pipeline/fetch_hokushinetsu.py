# -*- coding: utf-8 -*-
"""北信越大学サッカー連盟（hufl.info）から大学サッカーの日程・結果を取得し、
data/leagues/<code>/ に正規化JSONとして保存する。

データ出典: 北信越大学サッカー連盟 (https://hufl.info/)
対象: 北信越大学サッカーリーグ1部・2部。
WordPressのテーブル（前期・後期で別テーブルだが同一ページに掲載）から取得する。
公式の順位表ページは公開されていないため、common.compute_standings で試合結果から
自前集計する（勝点3・分1・敗0、得失点差順）。
未消化の試合はスコアセルが "&#8211;"（enダッシュ）のみになる。
"""
import html as html_lib
import json
import re
from datetime import date, datetime
from pathlib import Path

from common import fetch, match_date_iso, compute_standings, build_teams
from team_slugs import slug_for

BASE = "https://hufl.info"
CURRENT_SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"

# (部) -> (リーグコード, 表示名, URLパス)
DIVISIONS = {
    1: ("hokushinetsu-1-2026", "北信越大学サッカーリーグ1部", "schedule-div1"),
    2: ("hokushinetsu-2-2026", "北信越大学サッカーリーグ2部", "schedule-div2"),
}

TABLE_RE = re.compile(r"<table>(.*?)</table>", re.DOTALL)
TR_RE = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.DOTALL)


def cell_text(td_html: str) -> str:
    s = re.sub(r"<[^>]+>", "", td_html or "")
    return html_lib.unescape(s).strip()


def league_url(path: str) -> str:
    return f"{BASE}/league/{path}/"


def parse_matches(html: str, category_label: str, season_start_year: int) -> list[dict]:
    matches = []
    for table_html in TABLE_RE.findall(html):
        rows = TR_RE.findall(table_html)
        for row in rows:
            cells = [cell_text(c) for c in TD_RE.findall(row)]
            if len(cells) != 6:
                continue  # ヘッダ行（<th>）はTD_REにマッチしないためスキップされる
            _round, date_s, home, score_s, away, venue = cells
            if not home or not away:
                continue
            dm = re.search(r"(\d{1,2})月(\d{1,2})日", date_s)
            if not dm:
                continue
            d_iso = match_date_iso(int(dm.group(1)), int(dm.group(2)), season_start_year)
            tm = re.search(r"(\d{1,2})[:;：](\d{2})", date_s)
            time_s = f"{tm.group(1)}:{tm.group(2)}" if tm else "未定"
            nums = re.findall(r"\d+", score_s)
            played = len(nums) >= 2
            hs, as_ = (int(nums[0]), int(nums[1])) if played else (None, None)
            matches.append({
                "id": f"{d_iso or 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
                "date": d_iso,
                "time": time_s,
                "category": category_label,
                "home": home,
                "away": away,
                "home_slug": slug_for(home),
                "away_slug": slug_for(away),
                "venue": venue or "未定",
                "status": "played" if played else "scheduled",
                "home_score": hs,
                "away_score": as_,
                "note": "",
            })
    return matches


def fetch_division(path: str, label: str, year: int = CURRENT_SEASON) -> dict | None:
    try:
        html = fetch(league_url(path))
    except Exception as e:
        print(f"  {label}: 取得失敗（{e}）")
        return None
    matches = parse_matches(html, label, year)
    if not matches:
        return None
    return {
        "matches": matches,
        "standings": compute_standings(matches, slug_for),
        "teams": build_teams(matches, slug_for),
        "label": label,
    }


def main() -> None:
    ok = 0
    for div, (code, label, path) in DIVISIONS.items():
        print(f"-- {label} ({code}) --")
        d = fetch_division(path, label)
        if d is None:
            print(f"{code}: データなし（取得失敗の可能性）")
            continue
        out_dir = DATA_DIR / code
        out_dir.mkdir(parents=True, exist_ok=True)
        played = sum(1 for m in d["matches"] if m["status"] == "played")
        meta = {
            "code": code,
            "region": "北信越",
            "gender": "男子",
            "group": "北信越大学サッカーリーグ",
            "league": label,
            "season_year": CURRENT_SEASON,
            "source": "北信越大学サッカー連盟",
            "source_url": league_url(path),
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
