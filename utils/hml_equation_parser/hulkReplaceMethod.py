import codecs
import json
import os
from typing import Dict, Tuple

with codecs.open(os.path.join(os.path.dirname(__file__),
                              "convertMap.json"),
                 "r", "utf8") as f:
    convertMap = json.load(f)

barDict = convertMap["BarConvertMap"]
matDict = convertMap["MatrixConvertMap"]
braceDict = convertMap["BraceConvertMap"]


def _findOutterBrackets(eqString: str, startIdx: int) -> Tuple[int, int]:
    '''
    eqString : equation string for converting.
    startIdx : the cursor of equation string to find brackets.
    return:
        (startCursor, endCursor) for outter brackets.
    '''
    idx = startIdx
    while True:
        idx -= 1
        if eqString[idx] == '{':
            break

    return _findBrackets(eqString, idx, direction=1)


def _findBrackets(eqString: str, startIdx: int, direction: int) -> Tuple[int, int]:
    '''
    eqString : equation string for converting.
    startIdx : the cursor of equation string to find brackets.
    direction : the direction of find.
        if 0, find brackets before the cursor.
           1, find brackets after the cursor.
    return:
        (startCursor, endCursor) for brackets.
    '''
    if direction == 1:
        startCur = eqString.find(r'{', startIdx)
        bracketCount = 1
        for i in range(startCur + 1, len(eqString)):
            if eqString[i] == r'{':
                bracketCount += 1
            elif eqString[i] == r'}':
                bracketCount -= 1

            if bracketCount == 0:
                return (startCur, i + 1)
    else:
        # reverse string and convert brackets.
        eqString = eqString[::-1]
        for idx, char in enumerate(eqString):
            if char == r'{':
                eqString = eqString[0:idx] + r'}' + eqString[idx + 1:]
            if char == r'}':
                eqString = eqString[0:idx] + r'{' + eqString[idx + 1:]

        # find brackets with new cursor
        newStartIdx = len(eqString) - (startIdx + 1)
        startCur, endCur = _findBrackets(eqString,
                                         newStartIdx,
                                         direction=1)
        return (len(eqString) - endCur,
                len(eqString) - startCur)

    raise ValueError("cannot find bracket")


def replaceAllBar(eqString: str) -> str:
    '''
    replace hat-like equation string.
    '''

    def replaceBar(eqString: str, barStr: str, barElem: str) -> str:
        cursor = 0

        while True:
            cursor = eqString.find(barStr)
            if cursor == -1:
                break
            try:
                eStart, eEnd = _findBrackets(eqString, cursor, direction=1)
                bStart, bEnd = _findOutterBrackets(eqString, cursor)
                elem = eqString[eStart:eEnd]

                beforeBar = eqString[0:bStart]
                afterBar = eqString[bEnd:]

                eqString = beforeBar + barElem + elem + afterBar
            except ValueError:
                return eqString
        return eqString

    for barKey, barElem in barDict.items():
        eqString = replaceBar(eqString, barKey, barElem)
    return eqString


def replaceAllMatrix(eqString: str) -> str:
    '''
    replace matrix-like equation
    '''

    def replaceElementsOfMatrix(bracketStr: str) -> str:
        '''
        replace the elements of matrix
        '''
        bracketStr = bracketStr[1:-1]  ## remove brackets

        bracketStr = bracketStr.replace(r'#', r' \\ ')
        bracketStr = bracketStr.replace(r'&amp;', r'&')

        return bracketStr

    def replaceMatrix(eqString: str, matStr: str, matElem: Dict[str, object]) -> str:
        cursor = 0
        while True:
            cursor = eqString.find(matStr)
            if cursor == -1:
                break
            try:
                eStart, eEnd = _findBrackets(eqString, cursor, direction=1)
                elem = replaceElementsOfMatrix(eqString[eStart:eEnd])

                if matElem['removeOutterBrackets'] == True:
                    bStart, bEnd = _findOutterBrackets(eqString, cursor)
                    beforeMat = eqString[0:bStart - len(matStr) - 1]
                    afterMat = eqString[bEnd:]
                else:
                    beforeMat = eqString[0:cursor]
                    afterMat = eqString[eEnd:]

                eqString = beforeMat[:cursor] + matElem['begin'] + \
                           elem + matElem['end'] + afterMat
            except ValueError:
                return eqString
        return eqString

    for matKey, matElem in matDict.items():
        eqString = replaceMatrix(eqString, matKey, matElem)
    return eqString


def replaceRootOf(eqString: str) -> str:
    '''
    `root {1} of {2}` -> `\sqrt[1]{2}`
    'root
    '''
    rootStr = r"root"
    ofStr = r"of"

    while True:
        rootCursor = eqString.find(rootStr)
        if rootCursor == -1:
            break
        try:
            ofCursor = eqString.find(ofStr)

            elem1 = _findBrackets(eqString, rootCursor, direction=1)
            elem2 = _findBrackets(eqString, ofCursor, direction=1)

            e1 = eqString[elem1[0] + 1:elem1[1] - 1]
            e2 = eqString[elem2[0] + 1:elem2[1] - 1]

            eqString = eqString[0:rootCursor] + \
                       r"\sqrt" + \
                       r"[" + e1 + r"]" + \
                       r"{" + e2 + r"}" + \
                       eqString[elem2[1] + 1:]
        except ValueError:
            return eqString
    return eqString


def _findBrackets2(eqString, cursor, direction=0):  # eqString에서 cursor 이후의 '{'와 '}'의 위치 찾음

    # direction = 0이면 cursor 앞에서 bracket 찾고 1이면 cursor 뒤에서 찾음

    if direction == 1:
        i = cursor + 1
        if "{" not in eqString[i:]: return False, False
        while True:
            if eqString[i] == "{":
                break
            i += 1

        if eqString[cursor + 1: i].strip() != "":  # root와 같은 단어와 {사이에 뭔가 있으면 그게 sqrt 안에 들어감(괄호 제대로 안쳐져 있던 경우)
            return False, False
        else:
            startCur = i
            i += 1
            while True:
                if eqString[i] == "}":
                    break
                i += 1
            endCur = i

    else:  # direction=0 일 때
        i = cursor - 1
        if "{" not in eqString[:i + 1]: return False, False

        while True:
            if eqString[i] == "}":
                break
            i -= 1

        endCur = i

        if eqString[i + 1:cursor].strip() != "":  # "}"와 root 사이에 뭔가 있으면 그게 sqrt 안에 들어감(괄호 제대로 안쳐져 있던 경우) ex) 1over4
            return False, False
        else:
            i = endCur - 1

            while True:
                if eqString[i] == "{":
                    break
                i -= 1
            startCur = i
    return startCur, endCur


def replaceRootOf2(eqString: str) -> str:
    '''
    `root {1} of {2}` -> `\sqrt[1]{2}`
    'root {3} -> \sqrt{3}

    '''

    hmlFracString = r"root"
    latexFracString = r"\sqrt"
    ofString = r"of"

    while True:
        cursor = eqString.find(hmlFracString)  # "over"시작 위치

        if cursor == -1:  # 더이상 root 단어가 존재하지 않음
            break

        ofCursor = eqString.find(ofString)

        # of 없을 때
        if ofCursor == -1 or ofCursor < cursor or hmlFracString in eqString[cursor:ofCursor]:

            start, end = _findBrackets2(eqString, cursor + 3, direction=1)  # of 뒤의 값을 구함

            if start:  # of 뒤에 brackets으로 묶여있을 때
                afterRoot = eqString[start:end + 1]
                i = 0

            else:  # root3과 같이 bracket 없음

                strList = eqString[cursor + 4:].split(" ")

                i = 0
                while True:
                    if strList[i] != " ":
                        afterRoot = strList[i]
                        break
                    i += 1

                    #######

            eqString = eqString[0:cursor] + latexFracString + "{" + afterRoot + "}" + " ".join(strList[i + 1:])

        else:  # of 있을 때
            start, end = _findBrackets2(eqString, ofCursor + 1, direction=1)  # of 뒤의 값을 구함

            if start:  # of 뒤에 brackets으로 묶여있을 때
                afterOf = eqString[start:end + 1]
                i = 0

            else:
                strList = eqString[ofCursor:].split(" ")
                if strList[0] != ofString:  # of2 와 같이 띄어쓰기가 되어있지 않는 경우
                    afterOf = strList[0][2:]
                else:
                    i = 1
                    while True:
                        if strList[i] != " ":
                            afterOf = strList[i]
                            break
                        i += 1

            eqString = eqString[0:cursor] + \
                       r"\sqrt" + \
                       r"[" + eqString[cursor + 4: ofCursor] + r"]" + \
                       r"{" + afterOf + r"}" + \
                       " ".join(strList[i + 1:])
    return eqString


def replaceFrac(eqString: str) -> str:
    '''
    `{1} over {2}` -> `\frac{1}{2}`
    '''
    hmlFracString = r"over"
    latexFracString = r"\frac"

    while True:
        cursor = eqString.find(hmlFracString)

        if cursor == -1:
            break
        try:
            # find numerator
            numStart, numEnd = _findBrackets(eqString, cursor, direction=0)
            numerator = eqString[numStart:numEnd]

            beforeFrac = eqString[0:numStart]
            afterFrac = eqString[cursor + len(hmlFracString):]

            eqString = beforeFrac + latexFracString + numerator + afterFrac
        except ValueError:
            return eqString
    return eqString


def replaceFrac_no_bracket(String):  # 3 over 4 -> \frac{3}{4}
    hmlFracString = r"over"
    latexFracString = r"\frac"

    strList = String.split(" ")
    cursor = strList.index(hmlFracString)
    numerator = "{" + strList[cursor - 1] + "}"
    denominator = "{" + strList[cursor + 1] + "}"

    return [latexFracString, numerator, denominator]


def replaceFrac2(eqString: str) -> str:
    '''
    `{1} over {2}` -> `\frac{1}{2}`
    '''
    hmlFracString = r"over"
    latexFracString = r"\frac"

    while True:
        cursor = eqString.find(hmlFracString)  # "over"시작 위치

        if cursor == -1:
            break

        # find numerator
        numStart, numEnd = _findBrackets2(eqString, cursor, direction=0)
        # numStart는 bracket { 위치, numEnd는 bracket }의 위치 +1

        strList = eqString[:cursor].split(" ")
        i = len(strList) - 1
        if numStart and eqString[numEnd + 1: cursor].strip() != "":  # "}"와 over사이에 있는것이 분자
            numerator = eqString[numEnd + 1:cursor].strip()
            beforeFrac = eqString[:numEnd + 1]
        elif numStart:
            numerator = eqString[numStart: numEnd + 1]
            beforeFrac = eqString[:numStart]
        elif eqString[cursor - 1] != " ":  # 4over3와 같이 분자가 over 앞에 붙어있음
            strList = eqString[:cursor].split(" ")
            numerator = strList[-1].strip()  # 분자
            beforeFrac = " ".join(strList[:len(strList) - 1])
        else:  # 4 over 3 과 같은 경우

            i = len(strList) - 1
            while True:

                if strList[i].strip() != "":
                    numerator = strList[i]
                    break
                i -= 1
            beforeFrac = " ".strList[:i]

        # find denominator
        numStart, numEnd = _findBrackets2(eqString, cursor + 3, direction=1)
        # numStart는 bracket { 위치, numEnd는 bracket }의 위치 +1
        j = 0
        if numStart and eqString[cursor + 4: numStart].strip() != "":  # over와 "{"사이에 있는것이 분모
            denominator = eqString[cursor + 4: numStart].strip()


        elif eqString[cursor + 1] != " ":  # 4over3와 같이 분모가 over 뒤에 붙어있음

            deStrList = eqString[cursor + 4:].split(" ")

            denominator = deStrList[0].strip()  # 분자

        else:  # 4 over 3 과 같은 경우

            deStrList = eqString[cursor + 4:].split(" ")

            j = 0

            while True:

                if deStrList[j] != " ":
                    denominator = deStrList[j]

                    break

                i += 1
        eqString = beforeFrac + latexFracString + "{" + numerator + "}" + "{" + denominator + "}" + " ".join(
            deStrList[j + 1:])
    # 2over3 -> \frac{2}{3}

    return eqString



def replaceAllBrace(eqString: str) -> str:
    '''
    replace (over, under)brace equation string.
    '''

    def replaceBrace(eqString: str, braceStr: str, braceElem: str) -> str:
        cursor = 0

        while True:
            cursor = eqString.find(braceStr)
            if cursor == -1:
                break
            try:
                eStart1, eEnd1 = _findBrackets(eqString, cursor, direction=1)
                eStart2, eEnd2 = _findBrackets(eqString, eEnd1, direction=1)
                elem1 = eqString[eStart1:eEnd1]
                elem2 = eqString[eStart2:eEnd2]

                beforeBrace = eqString[0:cursor]
                afterBrace = eqString[eEnd2:]

                eqString = beforeBrace + braceElem + elem1 + '^' + elem2 + afterBrace
            except ValueError:
                return eqString
        return eqString

    for braceKey, braceElem in braceDict.items():
        eqString = replaceBrace(eqString, braceKey, braceElem)
    return eqString
