import cv2
from sewar import mse, msssim, rmse_sw
import face_recognition
import numpy as np
from ValidImage import checkValidation, encoding
from PIL import Image
import image_similarity_measures
from image_similarity_measures.quality_metrics import rmse, psnr, ssim


def imageSimilarity(url1, url2):

    image1 = cv2.imread(url1)
    image2 = cv2.imread(url2)
    image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    face_location1 = face_recognition.face_locations(image1)
    face_location2 = face_recognition.face_locations(image2)

    top1, right1, bot1, left1 = face_location1[0]
    top2, right2, bot2, left2 = face_location2[0]

    try:

        out_ssim = ssim(image1[top1:bot1, left1:right1],
                        image2[top1:bot1, left1:right1])

        if(out_ssim < 0):

            return 0

        return float(out_ssim)
    except:
        return 0
