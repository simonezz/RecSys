import io

import matplotlib
import matplotlib.pyplot as plt
from PIL import Image, ImageChops

'''
latex 형식의 string을 complie하여 이미지 형태로 나오는 method
'''
white = (255, 255, 255, 255)

matplotlib.use("pgf")

matplotlib.rcParams.update({'text.latex.unicode': True})

matplotlib.rcParams.update(
    {'pgf.preamble': [r"\usepackage{kotex}", r"\usepackage{kotex-logo}", r"\usepackage[utf8x]{inputenc}"]})


def latex_to_img(tex):
    buf = io.BytesIO()
    plt.rc('text', usetex=True)
    plt.rc('font', family='kotex')
    plt.axis('off')
    plt.text(0.05, 0.5, f'${tex}$', size=20)
    plt.savefig(buf, format='png')
    plt.close()

    im = Image.open(buf)
    bg = Image.new(im.mode, im.size, white)
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    # plt.imshow(im.crop(bbox))
    # plt.show()
    (im.crop(bbox)).save("image1.png")  # 이미지 저장

    return


if __name__ == "__main__":
    # latex_to_img("안녕" + r'\frac{x}{y^2}')
    # latex_to_img("함수의 극한에 대한 설명으로 옳은 것만을 에서 있는 대로 고른 것은? ㄱ.  \\lim_{x \\rightarrow a} f(x) 와" )
    latex_to_img("안녕하세요 \\frac{x}{y}")
