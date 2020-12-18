import codecs
import json
import os
from typing import List

from hulkReplaceMethod import replaceAllMatrix, replaceAllBar, replaceAllBrace, replaceFrac2, replaceRootOf2

with codecs.open(os.path.join(os.path.dirname(__file__),
                              "convertMap.json"),
                 "r", "utf8") as f:
    convertMap = json.load(f)


def replaceOthers(strConverted):  # frac, brace 등등 대체

    # strConverted = ' '.join(strList)

    strConverted = replaceFrac2(strConverted)
    strConverted = replaceRootOf2(strConverted)
    strConverted = replaceAllMatrix(strConverted)
    strConverted = replaceAllBar(strConverted)
    strConverted = replaceAllBrace(strConverted)

    return strConverted



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

    strConverted = hmlEqStr.replace("\n", " \n ")
    strConverted = strConverted.replace('`', ' ')
    strConverted = strConverted.replace('{', ' { ')
    strConverted = strConverted.replace('}', ' } ')
    strConverted = strConverted.replace('&', ' & ')
    # strConverted = strConverted.replace("{ ", "{")
    # strConverted = strConverted.replace(" }", "}")
    strConverted = strConverted.replace("  ", " ")

    # strList = strConverted.split(' ')

    for c in convertMap["convertMap"]:
        strConverted.replace(c, convertMap['convertMap'][c])

    for c in convertMap["middleConvertMap"]:
        strConverted.replace(c, convertMap['middleConvertMap'][c])
    #
    #
    #
    # for key, candidate in enumerate(strList):
    #     if candidate in convertMap["convertMap"]:
    #         strList[key] = convertMap["convertMap"][candidate]
    #     elif candidate in convertMap["middleConvertMap"]:
    #         strList[key] = convertMap["middleConvertMap"][candidate]

    # strList = [string for string in strList if len(string) != 0]
    # strList = replaceBracket(strList)

    # if "=" in strConverted:
    #     strConverted = replaceOthers(strConverted)
    # if "=" in strList:  # 좌우변 따로 있는 경우
    #     equal_index = strList.index("=")
    #     # 좌우변 따로 처리
    #     strConverted = replaceOthers(strList[:equal_index]) + " = " + replaceOthers(strList[equal_index + 1:])
    #
    # else:
    #
    #     strConverted = replaceOthers(strList)

    strConverted = replaceOthers(strConverted)

    strConverted = strConverted.replace("<", "\\langle")
    strConverted = strConverted.replace(">", "\\rangle")

    return strConverted.replace("  ", " ")


def main(string):
    # result = ""
    # strList = string.split("=")
    # for s in strList:
    #     result += hmlEquation2latex(s)
    print(hmlEquation2latex(string))
    return hmlEquation2latex(string)


if __name__ == "__main__":
    # print(hmlEquation2latex("root 4 of  ab^2  `× root 3 of { a^2 b^3 } `÷ root 4 of { a^3 b^2 } 을 간단히 하면?"))
    # print(hmlEquation2latex("함수 \nf( x )=cases{ {rootx+3 -2}overx-1 &(x !=1)#~~~~````a &( x=1 )\n이 \nx=1\n에서 연속일 때, 상수 \na\n의 값은?\n① \n1over5\n② \n1over4\n③ \n1over3\n④ \n1over2\n⑤ \n1\n\n\n'"))
    # main("함수 \nf( x )=cases{ {rootx+3 -2}overx-1 &(x !=1)#~~~~````a &( x=1 )\n이 \nx=1\n에서 연속일 때, 상수 \na\n의 값은?\n① \n1over5\n② \n1over4\n③ \n1over3\n④ \n1over2\n⑤ \n1\n\n\n")
    # main("1over5")
    main("함수 \nf( x )={rootx+3 -2}overx-1 ")
