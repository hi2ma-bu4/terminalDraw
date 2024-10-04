"""
terminal描画関連ライブラリ
"""

from typing import Optional, Union, Any, Callable, Dict, List, Final, final
from dataclasses import dataclass

from shutil import get_terminal_size
from os import system
from re import search
from time import sleep

import eastAsianWidthOverride as ewo
from romaji import Romaji
import convenientFunc as cf

# type aliases
ta_Pos = Union[int, Callable[[Any], int]]
ta_RePos = Optional[ta_Pos]
ta_Draw = Union["DrawSquare", "DrawText", "DrawTableText"]
ta_ListText = List[List[str]]
ta_keyDict = Dict[str, str]

# ここまで


def s_join(l: List[str]) -> str:
    """
    文字列リストを結合
    """
    if not len(l):
        return ""
    return "".join(l)


def jpReplace(s: str, jpMode: int) -> str:
    """
    日本語入力用に置換
    """
    if ewo.slen(s) >= 1 and s[-1] != "\u0000":
        if jpMode == 0:
            s = s.replace("\u0000", "")
        elif jpMode == 1:
            tmp = s.split("\u0000")
            s = tmp[0]+Romaji.Romaji2Hira(tmp[1])
        elif jpMode == 2:
            tmp = s.split("\u0000")
            s = tmp[0]+Romaji.Romaji2Kata(tmp[1])
    else:
        s = s.replace("\u0000", "")
    return s


def maxStrLen(l: List[str]) -> int:
    return ewo.slen(max(l, key=lambda x: ewo.slen(x)))


@final
class _tsDict:
    """
    ターミナルサイズ管理
    """

    def __init__(self) -> None:
        self.column = 0
        self.line = 0

    def renewal(self) -> None:
        """
        ターミナルサイズ更新
        """
        ts = get_terminal_size()
        self.column = ts.columns - ts.columns % 2
        self.line = ts.lines-1


class Draw:
    """
    描画基底クラス
    """

    def __init__(self, x: ta_Pos = 1, y: ta_Pos = 1, sx: ta_Pos = 0, sy: ta_Pos = 0) -> None:
        """
        初期位置等設定
        """
        self.x = x
        self.y = y
        self.sx = sx
        self.sy = sy

    def renewal(self, x: ta_RePos = None, y: ta_RePos = None, sx: ta_RePos = None, sy: ta_RePos = None) -> None:
        """
        描画位置更新
        """
        if x != None:
            self.x = x
        if y != None:
            self.y = y
        if sx != None:
            self.sx = sx
        if sy != None:
            self.sy = sy

    def _getPosition(self, pos: ta_Pos, tsd: _tsDict) -> int:
        """
        描画位置取得
        """
        if isinstance(pos, int):
            return pos
        else:
            return pos(tsd)

    def renewalPos(self, tsd: _tsDict) -> None:
        """
        描画位置更新
        """
        self.posX = self._getPosition(self.x, tsd)
        self.posSX = self._getPosition(self.sx, tsd)
        self.posY = self._getPosition(self.y, tsd)
        self.posSY = self._getPosition(self.sy, tsd)

    def draw(self, tsd: _tsDict) -> None:
        """
        描画
        """
        self.renewalPos(tsd)


class DrawSquare(Draw):
    """
    矩形描画
    """

    def draw(self, tsd: _tsDict) -> None:
        """
        描画
        """
        super().draw(tsd)

        maxY = self.posY + self.posSY

        for l in range(self.posY, maxY):
            print(f"\033[{l};{self.posX}H", end="")
            if l == self.posY or l == maxY-1:
                print("#"*self.posSX, end="")
            else:
                print("#"+" "*(self.posSX-2)+"#", end="")


class DrawText(Draw):
    """
    文字描画
    """

    def __init__(self, x: ta_Pos = 0, y: ta_Pos = 0, sx: ta_Pos = 0, sy: ta_Pos = 0, text: str = "") -> None:
        super().__init__(x, y, sx, sy)
        self.changeText(text)
        self.jpMode = 0

    def changeText(self, text: str) -> None:
        """
        文字更新
        """

        if text.count("\u0000") == 0:
            text = "\u0000" + text

        self.control_text = text
        self.text = text.replace(r"\u0000", "")

    def getText(self) -> str:
        """
        文字取得
        """
        return jpReplace(self.control_text, self.jpMode)

    def draw(self, tsd: _tsDict) -> None:
        """
        描画
        """
        super().draw(tsd)

        spText = jpReplace(self.control_text, self.jpMode).split("\n")

        i = 0
        for l in range(self.posY, self.posY+max(self.posSY, len(spText))):
            print(f"\033[{l};{self.posX}H", end="")
            if i < len(spText):
                print(ewo.center(spText[i], self.posSX), end="")
                i += 1


class DrawTableText(DrawText):
    """
    テーブル描画
    """

    ewo_dict: Final[Dict[str, Callable[[str, int], str]]] = {
        "c": ewo.center,
        "l": ewo.ljust,
        "r": ewo.rjust,
    }

    def __init__(self, x: ta_Pos = 0, y: ta_Pos = 0, sx: ta_Pos = 0, sy: ta_Pos = 0, listText: ta_ListText = [], settingList: List[List[Union[int, str]]] = []) -> None:
        super().__init__(x, y, sx, sy)
        self.listText = listText
        self.settingList = settingList
        self.scroll = 0

    def changeListText(self, listText: ta_ListText) -> None:
        """
        文字リスト(csv)更新
        """
        self.listText = listText

    def listScroll(self, num: int) -> int:
        """
        リストをスクロールさせる
        """
        self.scroll += num
        if self.scroll < 0:
            self.scroll = 0
        return self.scroll

    def draw(self, tsd: _tsDict) -> None:
        """
        描画
        """
        self.renewalPos(tsd)

        listTextLen = len(self.listText)

        if listTextLen > 0:
            if len(self.listText[0]) != len(self.settingList):
                input("リスト長の不一致")
                return
        else:
            return

        minLineSize = min(listTextLen, self.posSY)

        if listTextLen-minLineSize <= self.scroll:
            self.scroll = listTextLen-minLineSize
        if listTextLen <= self.posSY:
            self.scroll = 0

        tmpText = ""
        for i in range(self.scroll, self.scroll+minLineSize):
            for j in range(len(self.settingList)):
                tmpText += DrawTableText.ewo_dict[str(self.settingList[j][1])](
                    str(self.listText[i][j]), int(self.settingList[j][0])) + " "
            tmpText += "\n"
        self.changeText(tmpText[:-1])

        super().draw(tsd)


class DrawObjStore:
    """
    描画オブジェクト管理
    """

    def __init__(self, keyDict: ta_keyDict) -> None:
        """
        キー配列設定
        """
        self.store: list[list[ta_Draw]] = []
        self.overLayerStore: list[bool] = []
        self.layerLen: int = 0
        self.tsd = _tsDict()
        self.oldTsd = _tsDict()
        self.keyDict = keyDict
        self._isObjChange: bool = False
        self.sleepTime = 1

    def addLayer(self, useFullScreen: bool = False) -> int:
        """
        レイヤー追加
        """
        self.store.append([])
        self.overLayerStore.append(useFullScreen)
        self.layerLen = len(self.store)
        return self.layerLen

    def removeLayer(self, ind: Optional[int] = None) -> int:
        """
        レイヤー削除
        """
        if ind == None:
            ind = -1
        self.store.pop(ind)
        self.overLayerStore.pop(ind)
        self.layerLen = len(self.store)
        self._isObjChange = True
        return self.layerLen

    def addObj(self, obj: ta_Draw, layerInd: Optional[int] = None) -> int:
        """
        描画オブジェクト追加
        """
        if layerInd == None:
            layerInd = self.layerLen
        self.store[layerInd-1].append(obj)
        self._isObjChange = True
        return len(self.store[layerInd-1])

    def getObj(self, objInd: Optional[int] = None, layerInd: Optional[int] = None) -> ta_Draw:
        """
        描画オブジェクト取得
        """
        if layerInd == None:
            layerInd = self.layerLen
        if objInd == None:
            objInd = -1
        return self.store[layerInd-1][objInd]

    def addStrObj(self, keyStr: str, allowKeyRegex: str = " -~", maxLen: int = 0, jpChange: bool = False, objInd: Optional[int] = None, layerInd: Optional[int] = None) -> Union[int, str]:
        """
        キー入力(リアルタイム)
        """
        tdTextObj = self.getObj(objInd=objInd, layerInd=layerInd)
        if isinstance(tdTextObj, DrawText):
            textData = [*tdTextObj.control_text]
            if keyStr == self.keyDict["ENTER"]:
                if len(textData) > 1:
                    return tdTextObj.getText()
            elif keyStr == self.keyDict["BACKSPACE"]:
                if len(textData) > 1:
                    if textData[-1] == "\u0000":
                        textData.pop(-2)
                    elif len(textData) > 1:
                        textData.pop()
            elif keyStr == self.keyDict["DELETE"]:
                textData = ["\u0000"]
            elif keyStr == self.keyDict["TAB"]:
                if jpChange:
                    textData = [*jpReplace(s_join(textData), tdTextObj.jpMode)]

                    textData.append("\u0000")
                    tdTextObj.jpMode = (tdTextObj.jpMode+1) % 3
            elif search(f"^[{allowKeyRegex}]$", keyStr):
                if ewo.slen(jpReplace(s_join(textData), tdTextObj.jpMode)) < maxLen or maxLen == 0:
                    textData.append(keyStr)
            if s_join(textData) != tdTextObj.control_text:
                self._isObjChange = True
                tdTextObj.changeText(s_join(textData))
            return 0
        return 1

    def popupDraw(self, text: str = "", *, sec: Optional[int] = None, waitFunc: Optional[Callable] = None, layerRemove: bool = False) -> None:
        """
        ポップアップ表示
        """

        waitFlag = 0

        if sec == None:
            sec = self.sleepTime
        else:
            waitFlag += 1

        spText = text.split("\n")
        strLen = maxStrLen(spText)
        self.addLayer()
        self.addObj(DrawSquare(lambda ts: int(ts.column/2)-int(strLen/2)-3,
                    lambda ts: int(ts.line/2)-int(len(spText)/2)-2, strLen+6, 4+len(spText)))
        self.addObj(DrawText(lambda ts: int(ts.column/2)-int(strLen/2)-2,
                    lambda ts: int(ts.line/2)-int(len(spText)/2), strLen+4, text=text))
        self.drawTerminal()
        self.removeLayer()

        if waitFunc != None:
            waitFlag += 2
            waitFunc()

        if waitFlag == 0 or waitFlag & 1:
            sleep(sec)
        if layerRemove:
            self.removeLayer()

    def displayChange(self) -> None:
        """
        描画オブジェクト変更
        """
        self._isObjChange = True

    def drawTerminal(self, obligation: bool = False) -> None:
        """
        描画処理実行
        """
        self.tsd.renewal()
        if self.oldTsd.column != self.tsd.column or self.oldTsd.line != self.tsd.line:
            obligation = True
            self.oldTsd.renewal()
            system("cls")
        if self._isObjChange or obligation:
            self._isObjChange = False

            olsInd = 1 + cf.listFind(list(reversed(self.overLayerStore)), True)

            for l in self.store[-olsInd:]:
                for d in l:
                    d.draw(self.tsd)
            print("\n\033[1;1H", end="")


@dataclass
class W_Color:
    """
    文字色
    """
    RESET: Final[str] = "\033[0m"
    BOLD: Final[str] = "\033[1m"
    DARK: Final[str] = "\033[2m"
    ITALIC: Final[str] = "\033[3m"
    UNDERLINE: Final[str] = "\033[4m"
    FLASH: Final[str] = "\033[5m"

    BLACK: Final[str] = "\033[30m"
    RED: Final[str] = "\033[31m"
    GREEN: Final[str] = "\033[32m"
    YELLOW: Final[str] = "\033[33m"
    BLUE: Final[str] = "\033[34m"
    PURPLE: Final[str] = "\033[35m"
    CYAN: Final[str] = "\033[36m"
    WHITE: Final[str] = "\033[37m"

    L_BLACK: Final[str] = "\033[90m"
    L_RED: Final[str] = "\033[91m"
    L_GREEN: Final[str] = "\033[92m"
    L_YELLOW: Final[str] = "\033[93m"
    L_BLUE: Final[str] = "\033[94m"
    L_PURPLE: Final[str] = "\033[95m"
    L_CYAN: Final[str] = "\033[96m"
    L_WHITE: Final[str] = "\033[97m"

    @classmethod
    def __getitem__(cls, key: str) -> str:
        return vars(cls)[key]
