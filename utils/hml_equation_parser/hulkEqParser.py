import codecs
import json
import os
from typing import List

from hulkReplaceMethod import replaceAllMatrix, replaceAllBar, replaceRootOf, replaceAllBrace, replaceFrac2

with codecs.open(os.path.join(os.path.dirname(__file__),
                              "convertMap.json"),
                 "r", "utf8") as f:
    convertMap = json.load(f)


def replaceOthers(strList):  # frac, brace 등등 대체

    strConverted = ' '.join(strList)

    strConverted = replaceFrac2(strConverted)
    strConverted = replaceRootOf(strConverted)
    strConverted = replaceAllMatrix(strConverted)
    strConverted = replaceAllBar(strConverted)
    strConverted = replaceAllBrace(strConverted)

    return strConverted


def strip_brackets(string):  # "pi}" 와 같은 건 convertMap.json에서 key값으로 존재하지 않음. pi로 바꾸고 \\pi로 매칭한다음 다시 \\pi}가 되어야함.

    a = 0
    b = len(string) + 1
    if "{" in string and "}" in string:
        a = string.index("{")
        b = string.index("}")
        if string[a:b].strip() in convertMap["convertMap"]:
            return "{" + convertMap["convertMap"][string[a:b].strip()] + "}"
        elif string[a:b].strip() in convertMap["middleConvertMap"]:
            return "{" + convertMap["middleConvertMap"][string[a:b].strip()] + "}"
        else:
            return string

    elif "{" in string:
        a = string.index("{")
        if string[a:b].strip() in convertMap["convertMap"]:
            return "{" + convertMap["convertMap"][string[a:b].strip()]
        elif string[a:b].strip() in convertMap["middleConvertMap"]:
            return "{" + convertMap["middleConvertMap"][string[a:b].strip()]
        else:
            return string

    elif "}" in string:
        b = string.index("}")
        if string[a:b].strip() in convertMap["convertMap"]:
            return convertMap["convertMap"][string[a:b].strip()] + "}"
        elif string[a:b].strip() in convertMap["middleConvertMap"]:
            return convertMap["middleConvertMap"][string[a:b].strip()] + "}"
        else:
            return string

    else:
        if string.strip() in convertMap["convertMap"]:
            return convertMap["convertMap"][string.strip()]
        elif string.strip() in convertMap["middleConvertMap"]:
            return convertMap["middleConvertMap"][string.strip()]
        else:
            return string
    return string


def hmlEquation2latex(hmlEqStr):
    '''
    Convert hmlEquation string to latex string.

    Parameters
    ----------------------
    hmlEqStr : str
        A hml equation string to be converted.
    
    Returns
    ----------------------
    out : str
        A converted latex string.
    '''

    def replaceBracket(strList: List[str]) -> List[str]:
        '''
        "\left {"  -> "\left \{"
        "\right }" -> "\right \}"
        '''
        for i, string in enumerate(strList):
            if string == r'{':
                if i > 0 and strList[i - 1] == r'\left':
                    strList[i] = r'\{'
            if string == r'}':
                if i > 0 and strList[i - 1] == r'\right':
                    strList[i] = r'\}'
        return strList

    strConverted = hmlEqStr.replace('`', ' ')
    strConverted = strConverted.replace('{', ' { ')
    strConverted = strConverted.replace('}', ' } ')
    strConverted = strConverted.replace('&', ' & ')
    strConverted = strConverted.replace("{ ", "{")
    strConverted = strConverted.replace(" }", "}")

    strList = strConverted.split(' ')

    for key, candidate in enumerate(strList):
        strList[key] = strip_brackets(candidate)

    strList = [string for string in strList if len(string) != 0]
    strList = replaceBracket(strList)

    if "=" in strList:  # 좌우변 따로 있는 경우
        equal_index = strList.index("=")
        # 좌우변 따로 처리
        strConverted = replaceOthers(strList[:equal_index]) + " = " + replaceOthers(strList[equal_index + 1:])

    else:

        strConverted = replaceOthers(strList)

    strConverted = strConverted.replace("<", "\\langle")
    strConverted = strConverted.replace(">", "\\rangle")

    return strConverted.replace("  ", " ")


if __name__ == "__main__":
    print(hmlEquation2latex("root 4 of  ab^2  `× root 3 of { a^2 b^3 } `÷ root 4 of { a^3 b^2 } 을 간단히 하면?"))
