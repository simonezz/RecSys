import codecs
import json
import os
from typing import List

from utils.hml_equation_parser.hulkReplaceMethod import replaceAllMatrix, replaceAllBar, replaceAllBrace, replaceFrac2, replaceRootOf2

with codecs.open(os.path.join(os.path.dirname(__file__),
                              "convertMap.json"),
                 "r", "utf8") as f:
    convertMap = json.load(f)


def replaceOthers(strConverted):  # frac, brace 등등 대체

    # strConverted = ' '.join(strList)

    strConverted = replaceFrac2(strConverted)
    # print("frac 변환 끝")
    strConverted = replaceRootOf2(strConverted)
    # print("root 변환 끝")
    strConverted = replaceAllMatrix(strConverted)
    # print("matrix 변환 끝")
    strConverted = replaceAllBar(strConverted)
    # print("allBar 변환 끝")
    strConverted = replaceAllBrace(strConverted)
    # print("allBrace 변환 끝")

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
    strConverted = strConverted.replace("  ", " ")

    for c in convertMap["convertMap"]:
        strConverted = strConverted.replace(c, convertMap['convertMap'][c])

    for c in convertMap["middleConvertMap"]:
        strConverted = strConverted.replace(c, convertMap['middleConvertMap'][c])


    strConverted = replaceOthers(strConverted)

    # strConverted = strConverted.replace("<", "\\langle")
    # strConverted = strConverted.replace(">", "\\rangle")
    strConverted = strConverted.replace("\\\\", "\\")

    return strConverted.replace("  ", " ")


def main(string):
    # print(hmlEquation2latex(string))
    # with open("test1.txt", "w") as f:
    #     f.write(hmlEquation2latex(string))
    return hmlEquation2latex(string)


if __name__ == "__main__":
    # print(hmlEquation2latex("root 4 of  ab^2  `× root 3 of { a^2 b^3 } `÷ root 4 of { a^3 b^2 } 을 간단히 하면?"))
    # print(hmlEquation2latex("함수 \nf( x )=cases{ {rootx+3 -2}overx-1 &(x !=1)#~~~~````a &( x=1 )\n이 \nx=1\n에서 연속일 때, 상수 \na\n의 값은?\n① \n1over5\n② \n1over4\n③ \n1over3\n④ \n1over2\n⑤ \n1\n\n\n'"))
    # main("함수 \nf( x )=cases{ {rootx+3 -2}overx-1 &(x !=1)#~~~~````a &( x=1 )\n이 \nx=1\n에서 연속일 때, 상수 \na\n의 값은?\n① \n1over5\n② \n1over4\n③ \n1over3\n④ \n1over2\n⑤ \n1\n\n\n")
    # main("1over5")
    # main("함수 \nf( x )={rootx+3 -2}overx-1 ")
    print(main("f(x)= {cases{{x  ^{2} +2x} over {sqrt {1+2x} - sqrt {1-2x}}&(x != 0)#````````````````````````````````a&(x=0)}}"))
        # "\n \n \n 함수 \n f(x)= HULKCASE { x+a ~~ & (x< -1) #x ^2 -b & (-1 \\leq x<1)#2x-c & (x \\geq 1) }   \r \n \n 가 실수 전체의 집합에서 연속이고 \n f(0)=-2 \r \n \n 일 때, 상수 \n a \r \n \n , \n b \r \n \n , \n c \r \n \n 의 합 \n a+b+c \r \n \n 의 값을 구하여라. \n \n ")
