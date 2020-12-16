import sys

sys.path.append('./hml_equation_parser')
import subprocess
from subprocess import PIPE
from hulkEqParser import hmlEquation2latex

'''
hwplib 자바 파일들을 이용해서 hwp파싱
'''
# # url_list = ['https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/m/1/1/0/8_11000_Hi36q_0_p.hwp']
# url_list = [
#     # 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/02012/9_32102012_XcJoR_ppb_p.hwp']
# url_list = ["https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/1/2/30106/9_31230106_NrEOt_MBm_p.hwp"]
#
# for url in url_list:
#
#     proc = subprocess.Popen(['java', '-jar', 'hwp.jar', url], stdin=PIPE, stdout=PIPE, stderr=PIPE)
#     output = proc.communicate()[0]  ## this will capture the output of script called in the parent script.
#     # print(output.decode('utf-8')) # 한글 텍스트 추출
#     # print(hmlEquation2latex(output.decode('utf-8')).split("\n"))출 # hwp형태 수식을 latex으로 변환
#     print(latex_to_img((hmlEquation2latex(output.decode('utf-8')).split("\n")[1:])))
url = "https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/Mo/MO_200706/h2/200706_In_A/23_p.hwp"


def hwp_parser(url):
    proc = subprocess.Popen(['java', '-jar', 'hwp.jar', url], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = proc.communicate()[0]  ## this will capture the output of script called in the parent script.
    # print(output.decode('utf-8')) # 한글 텍스트 추출
    # print(hmlEquation2latex(output.decode('utf-8')).split("\n"))출 # hwp형태 수식을 latex으로 변환
    return " ".join((hmlEquation2latex(output.decode('utf-8')).split("\n")[1:]))


if __name__ == "__main__":
    hwp_parser(url)
