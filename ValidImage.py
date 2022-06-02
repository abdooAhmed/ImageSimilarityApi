from multiprocessing.dummy import Array
from typing import List
import face_recognition
import numpy
from sqlalchemy import true


def checkValidation(image):
    image = numpy.asarray(image)
    face_location = face_recognition.face_locations(image)

    if len(face_location) == 1:
        return True
    elif len(face_location) > 1:
        return f'there are {len(face_location)} person in image'
    else:
        return 'there is no person in image'


def encoding(image):
    image = numpy.asarray(image)
    imageEncode = numpy.array(face_recognition.face_encodings(image))

    print(imageEncode)
    return imageEncode


def compare(encode1, encode2):
    result = face_recognition.compare_faces(encode1, encode2)
    return result[0]
