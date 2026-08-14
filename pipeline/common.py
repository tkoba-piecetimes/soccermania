# -*- coding: utf-8 -*-
"""3地域（関西・東北・北信越）の取得スクリプトで共有するヘルパー。"""
import sys
import time
import urllib.error
import urllib.request
from datetime import date

UA = "Mozilla/5.0 (compatible; SoccerManiaBot/1.0)"


def fetch(url: str, retries: int = 2, encoding: str = "utf-8") -> str:
    """礼儀正しい取得（失敗時は1回だけリトライ）。関西学生サッカー連盟のページは
    Shift_JISで配信されているため encoding 引数で切り替える。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                raw = res.read()
            time.sleep(1)  # 礼儀正しい取得: 1秒sleep
            return raw.decode(encoding, errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == retries - 1:
                raise
            print(f"[warn] fetch failed ({e}), retrying in {10 * (attempt + 1)}s...", file=sys.stderr)
            time.sleep(10 * (attempt + 1))


def match_date_iso(month: int, day: int, season_start_year: int) -> str | None:
    # 大学サッカーのシーズンは4月開幕〜12月（1-3月に食い込むことは基本ないが、
    # ラグビー版と同じ安全側の処理として1-3月は年をまたぐ扱いにしておく）。
    year = season_start_year + 1 if month <= 3 else season_start_year
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def compute_standings(matches: list[dict], slug_for) -> dict[str, list[dict]]:
    """試合結果から勝ち点（勝3・分1・敗0）と得失点差で順位表を算出する。
    関西学生サッカー連盟のように公式の順位表HTMLが別途存在するリーグでは
    そちらを優先し、東北・北信越のように公式順位表が公開されていないリーグの
    参考値としてこの関数を用いる。"""
    teams: dict[str, dict] = {}
    for m in matches:
        if m["status"] != "played":
            continue
        for team, gf, ga in ((m["home"], m["home_score"], m["away_score"]),
                             (m["away"], m["away_score"], m["home_score"])):
            e = teams.setdefault(team, {"team": team, "slug": slug_for(team),
                                        "points": 0, "games": 0, "wins": 0,
                                        "draws": 0, "losses": 0, "gf": 0, "ga": 0})
            e["games"] += 1
            e["gf"] += gf
            e["ga"] += ga
            if gf > ga:
                e["wins"] += 1
                e["points"] += 3
            elif gf == ga:
                e["draws"] += 1
                e["points"] += 1
            else:
                e["losses"] += 1
    entries = sorted(teams.values(),
                     key=lambda e: (-e["points"], -(e["gf"] - e["ga"]), -e["gf"]))
    for i, e in enumerate(entries, 1):
        e["rank"] = i
        diff = e["gf"] - e["ga"]
        e["goal_diff"] = f"+{diff}" if diff > 0 else str(diff)
        e["goals_for"] = e["gf"]
    return {"総合": entries}


def build_teams(matches: list[dict], slug_for) -> dict[str, dict]:
    teams = {}
    for m in matches:
        for team in (m["home"], m["away"]):
            teams.setdefault(team, {"team": team, "slug": slug_for(team),
                                    "block": "総合"})
    return teams
