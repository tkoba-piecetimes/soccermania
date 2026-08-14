# -*- coding: utf-8 -*-
"""東北サッカー協会（jfa.jp内の東北地区ページ）から大学サッカーの日程・結果を取得し、
data/leagues/<code>/ に正規化JSONとして保存する。

データ出典: 東北サッカー協会 (https://www.jfa.jp/match_47fa/102_tohoku/)
対象: 東北地区大学サッカーリーグ1部・2部（3部は存在しない。3部相当のURLは404）。
公式の順位表ページは公開されていないため、common.compute_standings で試合結果から
自前集計する（勝点3・分1・敗0、得失点差順）。
試合表は `table_jfa-match-center` クラスのテーブルで、不戦勝（棄権）の場合は
スコアセルに "(棄権)" の注記が入る。未消化の試合はスコアセルが "-" のみになる。
"""
import json
import re
from datetime import date, datetime
from pathlib import Path

from common import fetch, match_date_iso, compute_standings, build_teams
from team_slugs import slug_for

BASE = "https://www.jfa.jp/match_47fa/102_tohoku"
CURRENT_SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"

# (部) -> (リーグコード, 表示名)
DIVISIONS = {
    1: ("tohoku-1-2026", "東北地区大学サッカーリーグ1部"),
    2: ("tohoku-2-2026", "東北地区大学サッカーリーグ2部"),
}

ROW_RE = re.compile(
    r'<td width=" 5%">\d+</td>\s*'
    r'<td width="10%">(.*?)</td>\s*'                              # 1 日程・時間
    r'<td class="txtL" width="20%"><div>([^<]*)</div></td>\s*'    # 2 会場
    r'<td width="23%">\s*<strong>([^<]+)</strong>.*?</td>\s*'     # 3 ホーム
    r'<td nowrap="nowrap" width="9%">(.*?)</td>\s*'               # 4 スコア
    r'<td width="23%">\s*<strong>([^<]+)</strong>.*?</td>',       # 5 アウェー
    re.DOTALL)


def strip_tags(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def season_url(div: int, year: int = CURRENT_SEASON) -> str:
    return f"{BASE}/{year}_university/div{div}/thfa/schedule.html"


def parse_date_time(cell_html: str) -> tuple[int | None, int | None, str]:
    text = strip_tags(cell_html)
    m = re.search(r"(\d{1,2})/(\d{1,2})\(", text)
    if not m:
        return None, None, "未定"
    tm = re.search(r"(\d{1,2}:\d{2})", text)
    return int(m.group(1)), int(m.group(2)), (tm.group(1) if tm else "未定")


def parse_matches(html: str, category_label: str, season_start_year: int) -> list[dict]:
    matches = []
    for dt_cell, venue, home, score_cell, away in ROW_RE.findall(html):
        home, away, venue = home.strip(), away.strip(), venue.strip()
        if not home or not away:
            continue
        month, day, time_s = parse_date_time(dt_cell)
        d_iso = match_date_iso(month, day, season_start_year) if month else None
        score_text = strip_tags(score_cell)
        nums = re.findall(r"\d+", score_text)
        played = len(nums) >= 2
        hs, as_ = (int(nums[0]), int(nums[1])) if played else (None, None)
        note = "不戦勝（棄権）" if "棄権" in score_text else ""
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
            "note": note,
        })
    return matches


def fetch_division(div: int, label: str, year: int = CURRENT_SEASON) -> dict | None:
    try:
        html = fetch(season_url(div, year))
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
    for div, (code, label) in DIVISIONS.items():
        print(f"-- {label} ({code}) --")
        d = fetch_division(div, label)
        if d is None:
            print(f"{code}: データなし（取得失敗の可能性）")
            continue
        out_dir = DATA_DIR / code
        out_dir.mkdir(parents=True, exist_ok=True)
        played = sum(1 for m in d["matches"] if m["status"] == "played")
        meta = {
            "code": code,
            "region": "東北",
            "gender": "男子",
            "group": "東北地区大学サッカーリーグ",
            "league": label,
            "season_year": CURRENT_SEASON,
            "source": "東北サッカー協会",
            "source_url": season_url(div),
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
