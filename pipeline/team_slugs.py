# -*- coding: utf-8 -*-
"""チーム名 → URLスラッグの対応表とスラッグ解決ロジック（サッカー版）。

解決順: 1) 手動登録の対応表  2) pykakasiによるローマ字化  3) ハッシュフォールバック
"""
import re
import sys

TEAM_SLUGS = {
    # ---- 関西学生サッカーリーグ 1部（jufa-kansai.jpは「○○大学」のフル表記） ----
    "京都産業大学": "kyoto-sangyo",
    "同志社大学": "doshisha",
    "関西大学": "kansai-u",
    "関西学院大学": "kwansei-gakuin",
    "立命館大学": "ritsumeikan",
    "阪南大学": "hannan",
    "桃山学院大学": "momoyama-gakuin",
    "大阪体育大学": "osaka-taiiku",
    "甲南大学": "konan",
    "大阪学院大学": "osaka-gakuin",
    "びわこ成蹊スポーツ大学": "biwako-seikei",
    "大阪商業大学": "osaka-shogyo",

    # ---- 東北地区大学サッカーリーグ（jfa.jp、「○○大学」のフル表記） ----
    "仙台大学": "sendai-u",
    "東日本国際大学": "higashinihon-kokusai",
    "富士大学": "fuji-u",
    "東北工業大学": "tohoku-kogyo",
    "八戸学院大学": "hachinohe-gakuin",
    "ノースアジア大学": "north-asia",

    # ---- 北信越大学サッカー連盟（hufl.info、末尾「大」の省略表記） ----
    "新潟医療福祉大": "niigata-iryo-fukushi",
    "松本大": "matsumoto",
    "新潟経営大": "niigata-keiei",
    "北陸大": "hokuriku",
    "金沢大": "kanazawa-u",
    "金沢学院大": "kanazawa-gakuin",
    "新潟産業大": "niigata-sangyo",
    "新潟大": "niigata-u",
}

_kks = None


def _romaji(name: str) -> str | None:
    global _kks
    try:
        if _kks is None:
            import pykakasi
            _kks = pykakasi.kakasi()
        base = re.sub(r"(大学院|大学|高校|高|大)$", "", name.strip())
        s = "".join(x["hepburn"] for x in _kks.convert(base))
        s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
        return s or None
    except Exception:
        return None


def slug_for(team: str) -> str:
    if team in TEAM_SLUGS:
        return TEAM_SLUGS[team]
    r = _romaji(team)
    if r:
        TEAM_SLUGS[team] = r
        return r
    print(f"[warn] スラッグ生成不可のチーム名: {team}", file=sys.stderr)
    return f"team-{abs(hash(team)) % 10**8}"
