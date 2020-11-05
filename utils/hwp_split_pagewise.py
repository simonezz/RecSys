# -*- coding : cp949 -*-
'''
hwp파일을 페이지 별로 쪼개서 저장하는 함수

** 윈도우에서만 가능하다.(win32com)
** 한글과컴퓨터가 제대로 설치가 되어 있지 않으면, win32.gencache.EnsureDispatch("HWPFrame.HwpObject")에서 Invalid Class String 에러가 난다.

'''

import os
from time import sleep
from tkinter.filedialog import askopenfilename

import win32com.client as win32


class Hwp:

    def __init__(self):
        self.hwp = win32.gencache.EnsureDispatch("HWPFrame.HwpObject")

    def __del__(self):
        self.hwp.Clear(option=1)  # 0:팝업, 1:버리기, 2:저장팝업, 3:무조건저장(빈문서#는 버림)
        self.hwp.Quit()

    def open_file(self, filename, view=False):
        self.name = filename
        self.hwp.RegisterModule("FilePathCheckDLL", "SecurityModule")
        if view == True:
            self.hwp.Run("FileNew")
        self.hwp.Open(self.name)

    def split_save(self):

        name = self.name
        self.hwp.MovePos(0)
        self.pagecount = self.hwp.PageCount
        hwp_docs = self.hwp.XHwpDocuments

        # target_folder = os.path.join(os.environ['USERPROFILE'], 'desktop', 'result')
        target_folder = os.path.join(os.environ['USERPROFILE'], 'desktop/result', name.split('.')[0])
        try:
            os.mkdir(target_folder)
        except FileExistsError:
            print(f"바탕화면에 {target_folder} 폴더가 이미 생성되어 있습니다.")

        for i in range(self.pagecount):
            hwp_docs.Item(0).SetActive_XHwpDocument()
            sleep(1)
            self.hwp.Run("CopyPage")
            sleep(1)
            hwp_docs.Add(isTab=True)
            hwp_docs.Item(1).SetActive_XHwpDocument()
            self.hwp.Run("Paste")
            self.hwp.SaveAs(
                os.path.join(target_folder, name.split(".")[0] + "_" + str(i + 1) + ".hwp"))
            self.hwp.Run("FileClose")
            self.hwp.Run("MovePageDown")
            print(f"{i + 1}/{self.pagecount}")

    def quit(self):
        self.hwp.Quit()


def main():
    name = askopenfilename(initialdir=os.path.join(os.environ["USERPROFILE"], "desktop"),
                           filetypes=(("아래아한글 파일", "*.hwp"), ("모든 파일", "*.*")),
                           title="HWP파일을 선택하세요.")

    hwp = Hwp()
    hwp.open_file(name)
    hwp.split_save(name)
    hwp.quit()

    print("완료")

    input()


if __name__ == "__main__":
    main()
