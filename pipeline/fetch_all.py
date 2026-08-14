# -*- coding: utf-8 -*-
"""関西・東北・北信越の3地区を順番に取得する。

関東は football-system.jp（robots.txtで全クローラー拒否）以外に構造化データの
取得先が見つからなかったため対象外（保留）。docs/soccer-sources.md参照。
"""
import fetch_hokushinetsu
import fetch_kansai
import fetch_tohoku


def main() -> None:
    print("=== 関西（jufa-kansai.jp）===")
    fetch_kansai.main()
    print("=== 東北（jfa.jp 東北地区）===")
    fetch_tohoku.main()
    print("=== 北信越（hufl.info）===")
    fetch_hokushinetsu.main()


if __name__ == "__main__":
    main()
