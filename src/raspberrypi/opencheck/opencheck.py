import cv2
from docopt import docopt
import glob
import logging
import os
import sys
import requests
import tempfile
import io

'''
読み込んだ画像と予め保持している画像の特徴点のマッチングを行う
引数 targetImagePath：調査対象画像のURL
返り値 ret：特徴点の距離（値が小さいほど類似度が高い）
'''
def PhotoImageMatching(targetImagePath):
    args = docopt(__doc__)
    #教師データ
    teacherImagePath = f"./comparephotodata/open.jpg"

    img_size = (800, 800)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    # detector = cv2.ORB_create()
    detector = cv2.AKAZE_create()

    # read teacher image
    teacherImage_name = os.path.basename(teacherImagePath)
    teacherImage = cv2.imread(teacherImagePath, cv2.IMREAD_GRAYSCALE)
    teacherImage = cv2.resize(teacherImage, img_size)
    (teacher_kp, teacher_des) = detector.detectAndCompute(teacherImage, None)

    # read target image
    tergetImage_name = os.path.basename(targetImagePath)
    #targetImage = cv2.imread(targetImagePath, cv2.IMREAD_GRAYSCALE)
    targetImage = imread_web(targetImagePath)
    targetImage = cv2.resize(targetImage, img_size)
    (target_kp, target_des) = detector.detectAndCompute(targetImage, None)

    # detect
    matches = bf.match(teacher_des, target_des)
    dist = [m.distance for m in matches]
    ret = sum(dist) / len(dist)

    return ret

'''
Webから画像読み込み
openCVの画像変数を返す
'''
def imread_web(url):
    res = requests.get(url)
    img = None

    with tempfile.NamedTemporaryFile(dir='./') as fp:
        fp.write(res.content)
        fp.file.seek(0)
        img = cv2.imread(fp.name)
    return img