"""
lenとかljust,rjust,centerを全角に対応させる
"""

from unicodedata import east_asian_width


def slen(text: str) -> int:
    """
    全角半角文字幅取得
    """
    cou = 0
    for c in text:
        if east_asian_width(c) in 'FWA':
            cou += 2
        else:
            cou += 1
    return cou


def _s(s: str, width: int) -> int:
    return max(width - slen(s), 0)


def ljust(s: str, width: int, fillchar: str = ' ') -> str:
    return s + fillchar * _s(s, width)


def rjust(s: str, width: int, fillchar: str = ' ') -> str:
    return fillchar * _s(s, width) + s


def center(s: str, width: int, fillchar: str = ' ') -> str:
    space = _s(s, width)
    r = space // 2
    L = space - r
    return fillchar * L + s + fillchar * r
