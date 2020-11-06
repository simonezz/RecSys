# -*- coding:utf-8 -*-
'''
hwp파일을 페이지 별로 쪼개서 저장하는 함수
** 윈도우에서만 가능하다.(win32com)
** 한글과컴퓨터가 제대로 설치가 되어 있지 않으면, win32.gencache.EnsureDispatch("HWPFrame.HwpObject")에서 Invalid Class String 에러가 난다.
'''
import os
from time import sleep
from tkinter.filedialog import askopenfilename

import win32com.client as win32

_this_folder_ = os.path.dirname(os.path.abspath(__file__))
_this_basename_ = os.path.splitext(os.path.basename(__file__))[0]


class HwpHandler:
    def __init__(self):
        self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    def __del__(self):
        self.hwp.Clear(option=1)  # 0:팝업, 1:버리기, 2:저장팝업, 3:무조건저장(빈문서#는 버림)
        self.hwp.Quit()

    def open_file(self, filename, view=False):
        self.name = filename
        self.fname = filename.split('/')[-1]

        # hwp보안모듈 승인(한컴에서 dll 다운받아야함)
        # https://www.martinii.fun/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EC%95%84%EB%9E%98%EC%95%84%ED%95%9C%EA%B8%80-%EB%B3%B4%EC%95%88%EB%AA%A8%EB%93%88-%EC%84%A4%EC%B9%98%EB%B0%A9%EB%B2%95%EA%B7%80%EC%B0%AE%EC%9D%80-%EB%B3%B4%EC%95%88%ED%8C%9D%EC%97%85-%EC%A0%9C%EA%B1%B0-1
        self.hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
        if view == True:
            self.hwp.Run("FileNew")
        self.hwp.Open(self.name)

    def split_page_and_save(self):
        self.hwp.MovePos(0)
        self.pagecount = self.hwp.PageCount
        hwp_docs = self.hwp.XHwpDocuments
        save_path = os.path.join(_this_folder_, self.fname.split('.')[0])
        # target_folder = os.path.join(os.environ['USERPROFILE'], 'desktop', 'result')
        # target_folder = os.path.join(os.environ['USERPROFILE'], 'desktop/result', name.split('.')[0])
        try:
            os.mkdir(save_path)
        except FileExistsError:
            print(f"{save_path} 폴더가 이미 생성되어 있습니다.")
        for i in range(self.pagecount):
            hwp_docs.Item(0).SetActive_XHwpDocument()
            sleep(1)
            # self.hwp.Run("SelectAll")
            # self.hwp.Run("Copy")
            self.hwp.Run("MovePageEnd")  # 현 페이지의 마지막으로 커서 옮김
            self.hwp.Run("CopyPage")  # 현재 페이지만 복사
            sleep(1)
            hwp_docs.Add(isTab=True)
            hwp_docs.Item(1).SetActive_XHwpDocument()
            self.hwp.Run("Paste")  # 복사한 페이지 붙여넣기
            self.hwp.SaveAs(
                os.path.join(save_path, self.fname.split(".")[0] + "_" + str(i + 1) + ".hwp"))  # 새로운 hwp파일로 저장
            self.hwp.Run("FileClose")
            self.hwp.Run("MovePageDown")
            print(f"{i + 1}/{self.pagecount}")
        print("HWP split and save success!")

    def quit(self):
        self.hwp.Quit()


# def parse_arguments():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-f', dest='file_name')
#     parser.add_argument('-p', dest='save_path')
#     result = parser.parse_args()
#     return result
def main():
    name = askopenfilename(initialdir=os.path.join(os.environ["USERPROFILE"], "desktop"),
                           filetypes=(("아래아한글 파일", "*.hwp"), ("모든 파일", "*.*")),
                           title="HWP파일을 선택하세요.")
    # args = parse_arguments()
    hwp = HwpHandler()
    hwp.open_file(name)
    hwp.split_page_and_save()
    hwp.quit()
    print("완료")
if __name__ == "__main__":
    main()