# -*- coding: utf-8 -*-
"""関西・東北・北信越・関東の4地区を順番に取得する。

関東は football-system.jp（robots.txtで全クローラー拒否）には一切アクセスせず、
連盟公式サイト jufa-kanto.jp が自前HTMLで公開している節別マッチレポートページから取得する
（pipeline/fetch_kanto.py参照）。docs/soccer-sources.md参照。
"""
import fetch_hokushinetsu
import fetch_kansai
import fetch_kanto
import fetch_tohoku


def main() -> None:
    print("=== 関西（jufa-kansai.jp）===")
    fetch_kansai.main()
    print("=== 東北（jfa.jp 東北地区）===")
    fetch_tohoku.main()
    print("=== 北信越（hufl.info）===")
    fetch_hokushinetsu.main()
    print("=== 関東（jufa-kanto.jp 節別マッチレポート）===")
    fetch_kanto.main()


if __name__ == "__main__":
    main()
