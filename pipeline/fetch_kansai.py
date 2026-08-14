# -*- coding: utf-8 -*-
"""関西学生サッカー連盟（jufa-kansai.jp）から大学サッカーの日程・結果・順位を取得し、
data/leagues/<code>/ に正規化JSONとして保存する。

データ出典: 関西学生サッカー連盟 (https://www.jufa-kansai.jp/)
対象: 関西学生サッカーリーグ 1部・2部（3部以下は対象外。docs/soccer-sources.md参照）。
ページはShift_JISで配信されている。順位表は
`/meet/student/{year:02d}data/team_rank_{bu}.html` に公式集計が公開されているため
そちらを正とし、日程・結果表 `/meet/student/{year:02d}data/nittei_{bu}_{half}.html`
（前期=1・後期=2。後期開幕前は404になるため取得できたものだけ使う）と合わせて使う。
"""
import json
import re
from datetime import date, datetime
from pathlib import Path

from common import fetch, match_date_iso, build_teams
from team_slugs import slug_for

BASE = "https://www.jufa-kansai.jp"
CURRENT_SEASON = 2026
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "leagues"

# (部) -> (リーグコード, 表示名)
DIVISIONS = {
    1: ("kansai-1-2026", "関西学生サッカーリーグ1部"),
    2: ("kansai-2-2026", "関西学生サッカーリーグ2部"),
}

RANK_ROW_RE = re.compile(
    r"<TR>\s*"
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 1 順位
    r"<TD[^>]*><FONT[^>]*>([^<]+)</FONT></TD>\s*"         # 2 チーム名
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 3 勝点
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 4 試合
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 5 勝数
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 6 分数
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 7 負数
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 8 総得点
    r"<TD[^>]*><FONT[^>]*>(\d+)<BR></FONT></TD>\s*"      # 9 総失点
    r"<TD[^>]*><FONT[^>]*>(-?\d+)<BR></FONT></TD>",       # 10 得失点差
    re.IGNORECASE | re.DOTALL)

MATCH_RE = re.compile(
    r"<td align=['\"]left['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>"
    r"<font class=['\"]fs_12['\"]>(\d{1,2})/(\d{1,2})[^<]*<br></font></td>\s*"
    r"<td align=['\"]center['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>\s*"
    r"<font class=['\"]fs_12['\"]>([^<]*)<br></font></td>\s*"
    r"<td align=['\"]center['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>"
    r"<font class=['\"]fs_12['\"]>([^<]+)<br></font></td>\s*"
    r"<td align=['\"]right['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>\s*"
    r"(.*?)</table></td>\s*"
    r"<td align=['\"]center['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>"
    r"<font class=['\"]fs_12['\"]>([^<]+)<br></font></td>\s*"
    r"<td align=['\"]center['\"] valign=['\"]middle['\"] class=['\"]matrix_[a-z0-9]+['\"]>"
    r"<font class=['\"]fs_12['\"]>([^<]+)<br></font></td>",
    re.IGNORECASE | re.DOTALL)


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "")


def rank_url(bu: int, year: int = CURRENT_SEASON) -> str:
    yy = year % 100
    return f"{BASE}/meet/student/{yy}data/team_rank_{bu}.html"


def nittei_url(bu: int, half: int, year: int = CURRENT_SEASON) -> str:
    yy = year % 100
    return f"{BASE}/meet/student/{yy}data/nittei_{bu}_{half}.html"


def parse_standings(html: str) -> list[dict]:
    entries = []
    for m in RANK_ROW_RE.finditer(html):
        rank, team, pts, games, wins, draws, losses, gf, ga, _diff_raw = m.groups()
        team = team.strip()
        gf_i, ga_i = int(gf), int(ga)
        diff = gf_i - ga_i  # 得失点差はスコア差から算出しなおす（表示の+符号を統一するため）
        entries.append({
            "rank": int(rank), "team": team, "slug": slug_for(team),
            "points": int(pts), "games": int(games), "wins": int(wins),
            "draws": int(draws), "losses": int(losses),
            "gf": gf_i, "ga": ga_i, "goals_for": gf_i,
            "goal_diff": f"+{diff}" if diff > 0 else str(diff),
        })
    return entries


def parse_matches(html: str, category_label: str, season_start_year: int) -> list[dict]:
    matches = []
    for mo, dd, time_raw, home, scoreblock, away, venue in MATCH_RE.findall(html):
        home, away, venue = home.strip(), away.strip(), venue.strip()
        if not home or not away:
            continue
        d_iso = match_date_iso(int(mo), int(dd), season_start_year)
        nums = re.findall(r"\d+", strip_tags(scoreblock))
        played = len(nums) >= 2
        hs, as_ = (int(nums[0]), int(nums[1])) if played else (None, None)
        t = time_raw.strip() or "未定"
        matches.append({
            "id": f"{d_iso or 'tbd'}-{slug_for(home)}-vs-{slug_for(away)}",
            "date": d_iso,
            "time": t,
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


def fetch_division(bu: int, label: str, year: int = CURRENT_SEASON) -> dict | None:
    matches: list[dict] = []
    for half in (1, 2):
        try:
            html = fetch(nittei_url(bu, half, year), encoding="shift_jis")
        except Exception as e:
            print(f"  {label} {'前期' if half == 1 else '後期'}: 取得失敗（{e}）")
            continue
        ms = parse_matches(html, label, year)
        matches.extend(ms)
        print(f"  {label} {'前期' if half == 1 else '後期'}: 試合{len(ms)}件")
    if not matches:
        return None
    try:
        rank_html = fetch(rank_url(bu, year), encoding="shift_jis")
        standings = parse_standings(rank_html)
    except Exception as e:
        print(f"  {label} 順位表: 取得失敗（{e}）", )
        standings = []
    return {
        "matches": matches,
        "standings": {"総合": standings} if standings else {"総合": []},
        "teams": build_teams(matches, slug_for),
        "label": label,
    }


def main() -> None:
    ok = 0
    for bu, (code, label) in DIVISIONS.items():
        print(f"-- {label} ({code}) --")
        d = fetch_division(bu, label)
        if d is None:
            print(f"{code}: データなし（取得失敗の可能性）")
            continue
        out_dir = DATA_DIR / code
        out_dir.mkdir(parents=True, exist_ok=True)
        played = sum(1 for m in d["matches"] if m["status"] == "played")
        meta = {
            "code": code,
            "region": "関西",
            "gender": "男子",
            "group": "関西学生サッカーリーグ",
            "league": label,
            "season_year": CURRENT_SEASON,
            "source": "関西学生サッカー連盟",
            "source_url": f"{BASE}/",
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
        print(f"{code}: {label} 試合{len(d['matches'])}件(結果{played}) "
              f"チーム{len(d['teams'])} 順位表{len(d['standings'].get('総合', []))}件")
        ok += 1
    print(f"done: {ok}/{len(DIVISIONS)} divisions")


if __name__ == "__main__":
    main()
