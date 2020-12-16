import argparse
import codecs
import json
import os
import sys
from xml.etree.ElementTree import fromstring, Element, ElementTree

import win32com.client as win32

from .hulkEqParser import hmlEquation2latex

'''
hwp파일을 hml파일로 변환 후 텍스트 파싱(수식제외)
'''
with codecs.open(os.path.join(os.path.dirname(__file__),
                              "config.json"),
                 "r", "utf8") as f:
    config = json.load(f)


class HwpMathParser:

    def __init__(self):
        self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    def open_file(self, filename, view=False):
        self.name = filename
        self.fname = filename.split('/')[-1]

        # hwp보안모듈 승인(한컴에서 dll 다운받아야함)
        # https://www.martinii.fun/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EC%95%84%EB%9E%98%EC%95%84%ED%95%9C%EA%B8%80-%EB%B3%B4%EC%95%88%EB%AA%A8%EB%93%88-%EC%84%A4%EC%B9%98%EB%B0%A9%EB%B2%95%EA%B7%80%EC%B0%AE%EC%9D%80-%EB%B3%B4%EC%95%88%ED%8C%9D%EC%97%85-%EC%A0%9C%EA%B1%B0-1
        self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")

        if view == True:
            self.hwp.Run("FileNew")
        self.hwp.Open(self.name)

    def save_as_hml(self, save_path):
        self.hwp.SaveAs(
            os.path.join(save_path, self.fname.split(".")[0] + ".hml"), "HML")  # 새로운 hwp파일로 저장
        print("hml로 변환하여 저장완료!")

        return save_path + '/' + self.fname.split(".")[0] + ".hml"

    def quit(self):
        self.hwp.Quit()


def parse_hml(xmlText):
    hwpml = fromstring(xmlText)
    body = hwpml.find("BODY")
    section = body.find("SECTION")

    docRoot = Element(config["NodeNames"]["root"])

    paragraphs = section.findall("P")

    for paragraph in paragraphs:

        paragraphNode = Element(config["NodeNames"]["paragraph"])

        if paragraph.get("PageBreak") == "true":
            paragraphNode.attrib[config["NodeAttributes"]["newPage"]] = "true"
        else:
            paragraphNode.attrib[config["NodeAttributes"]["newPage"]] = "false"

        # I suupposed that there is one text tag or no text tag in one paragraph.
        # If there are more than one text, you must use `findall` method to find all text tags.

        text = paragraph.find("TEXT")
        if text is not None:
            for child in text.getchildren():
                if child.tag == "CHAR":
                    value = child.text

                    if value is not None:  # For EQUATION tag, there is a </CHAR> tag and it has no information.
                        leafNode = Element(config["NodeNames"]["char"])
                        leafNode.text = value
                        paragraphNode.append(leafNode)

                elif child.tag == "EQUATION":
                    script = child.find("SCRIPT")
                    value = script.text

                    leafNode = Element(config["NodeNames"]["equation"])
                    leafNode.text = value
                    paragraphNode.append(leafNode)

                else:
                    print("not supported tag: {}".format(child.tag))

            docRoot.append(paragraphNode)

    return ElementTree(docRoot)


def convertEquation(doc):
    '''
    Convert equation with sample ElementTree.
    '''
    for paragraph in doc.findall(config["NodeNames"]["paragraph"]):
        for child in paragraph.getchildren():
            if child.tag == config["NodeNames"]["equation"]:
                child.text = hmlEquation2latex(child.text)
    return doc


def extract2HtmlStr(doc):
    '''
    Convert sample ElementTree to html
    '''

    def convertSpace2nbsp(string: str) -> str:
        return string.replace(' ', r'&nbsp;')

    htmlStringList = []

    for paragraph in doc.findall(config["NodeNames"]["paragraph"]):
        paragraphStringList = []

        if paragraph.get(config["NodeAttributes"]["newPage"]) == "true":
            paragraphStringList.append("<br>======================<br>")

        for child in paragraph.getchildren():
            if child.tag == config["NodeNames"]["char"]:
                paragraphStringList.append(convertSpace2nbsp(child.text))
            elif child.tag == config["NodeNames"]["equation"]:
                paragraphStringList.append("$" + child.text + "$")
        paragraphString = ''.join(paragraphStringList)
        htmlStringList.append(paragraphString)
    return config["htmlHeader"] + '<br>\n'.join(htmlStringList) + config["htmlFooter"]


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='file_name')
    parser.add_argument('-p', dest='save_path')
    result = parser.parse_args()
    return result


def main():
    script, hmlDoc, dst = sys.argv

    args = parse_arguments()

    hwp = HwpMathParser()

    hwp.open_file(args.file_name)  # hwp파일을 연다.

    hmlname = hwp.save_as_hml(args.save_path)  # hml파일로 저장한다.

    hwp.quit()

    xmlText = open(hmlname, 'r').read()  # hml파일을 연다.

    elementTree = parse_hml(xmlText)

    doc = convertEquation(elementTree)  # equation 변형

    doc.write(dst + '.xml')

    # with codecs.open(dst + ".html", "w", "utf8") as f:
    #     f.write(extract2HtmlStr(doc))
    print(extract2HtmlStr(doc))


if __name__ == "__main__":
    main()
    print("success")
