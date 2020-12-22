import sys

# sys.path.append('./hml_equation_parser')
import subprocess
from subprocess import PIPE
from utils.hml_equation_parser import hulkEqParser

'''
hwplib 자바 파일들을 이용해서 hwp파싱
'''

# url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/1/2/10312/9_31210312_TML5i_rbCp.hwp'
# url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03003/32103003_601_59_fv5brvd5_p.hwp'
# url = "https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03003/32103003_601_156_w96mfbs9_p.hwp"
# url = " https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03018/9_32103018_BUJ2r_-46Y_p.hwp"
# url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03018/9_32103018_BUJ2r_-46Y_p.hwp'
# url = "https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/h/2/1/03103/9_32103103_MUv4N_yM3_p.hwp"
# url = "https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/191023/arn4ch3o4b5lfg2z_p.hwp"
# url = " https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/Mo/MO_200711/h3/200711_Ha_B/3_p.hwp"
# url = " https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/Mo/MO_201810/h3/201810_Se_A/15_p.hwp"
url = "https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/m/2/1/1/9_21001_LxJ0H_5_p.hwp"

def hwp_parser(url):
    sys.path.append('./hml_equation_parser')
    proc = subprocess.Popen(
        ['java', '-jar', '/home/ubuntu/Recommender_SH/utils/hwp.jar', url],
        stdin=PIPE, stdout=PIPE, stderr=PIPE)
    output = proc.communicate()[0]  ## this will capture the output of script called in the parent script.

    txt = output.decode('utf-8')
    print("original: ", txt)
    parsing_txt = hulkEqParser.hmlEquation2latex(" ".join(txt.split("\n")[1:]))


    # print(txt_list)
    # print(" ".join(txt_list))
    # with open("test1.txt", "w") as f:
    #     f.write(" ".join(txt_list))
    return parsing_txt


if __name__ == "__main__":
    print("after parsing: ", hwp_parser(url))
