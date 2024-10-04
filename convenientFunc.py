"""
便利関数
"""

from typing import List, Any


def listFind(l: List[Any], x: Any) -> int:
    """
    String専用のfindをlistでも使用出来るようにした関数
    """
    if x in l:
        return l.index(x)
    else:
        return -1
