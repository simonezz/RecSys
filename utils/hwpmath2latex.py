import sys

sys.path.append('./hml_equation_parser')
import subprocess
from subprocess import PIPE
from hml_equation_parser.hulkEqParser import hmlEquation2latex

'''
hwplib 자바 파일들을 이용해서 hwp파싱
'''

# url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/1/2/10312/9_31210312_TML5i_rbCp.hwp'
url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03003/32103003_601_59_fv5brvd5_p.hwp'


def hwp_parser(url):
    sys.path.append('./hml_equation_parser')
    proc = subprocess.Popen(
        ['java', '-jar', '/home/master/source/project/Recommender_SH/Recommender-System/utils/hwp.jar', url],
        stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = proc.communicate()[0]  ## this will capture the output of script called in the parent script.
    # print(output.decode('utf-8')) # 한글 텍스트 추출
    # print(hmlEquation2latex(output.decode('utf-8')).split("\n"))출 # hwp형태 수식을 latex으로 변환
    txt_list = hmlEquation2latex(output.decode('utf-8')).split("\n")[1:]

    for i, t in enumerate(txt_list[:5]):
        try:
            if t[0] == '[':
                del txt_list[i]
        except:
            pass

    return " ".join(txt_list)
    # return " ".join((hmlEquation2latex(output.decode('utf-8')).split("\n")[1:]))


if __name__ == "__main__":
    hwp_parser(url)
