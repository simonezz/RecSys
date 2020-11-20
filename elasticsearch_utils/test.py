import sys

sys.path.append('../utils')
from hwp_parser import *
from urllib.request import Request, urlopen
import olefile

hwp_url = 'https://s3.ap-northeast-2.amazonaws.com/mathflat/math_problems/hwp/9/m/1/1/0/8_11000_Hi36q_0_p.hwp'
tmp = Request(hwp_url)
tmp = urlopen(tmp).read()

f = olefile.OleFileIO(tmp)

hwpReader = HwpReader(f)
