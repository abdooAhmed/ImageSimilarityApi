

import os

import image_similarity_measures
from ValidImage import checkValidation, encoding, compare
import numpy as np
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
from sqlalchemy import true
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request, Response
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from typing import List
from lan import getLoaction
import ast
import threading
from simlarity import imageSimilarity
from datetime import date
import time
from flask_cors import CORS

executor = ThreadPoolExecutor(2)
app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
    os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Init db
db = SQLAlchemy(app)
# Init ma
ma = Marshmallow(app)

# Product Class/Model


class Images(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, )
    ReportType = db.Column(db.Integer, )
    mimetype = db.Column(db.Text)
    imageEncode = db.Column(db.Text)
    imageURL = db.Column(db.Text)
    UserId = db.Column(db.Text)
    ReportId = db.Column(db.Integer, )

    def __init__(self, name, ReportType, mimetype, imageURL, imageEncode, UserId, ReportId):
        self.name = name
        self.ReportType = ReportType
        self.mimetype = mimetype
        self.imageEncode = imageEncode
        self.imageURL = imageURL
        self.UserId = UserId
        self.ReportId = ReportId


class RelatedReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    LostId = db.Column(db.Integer)
    FoundId = db.Column(db.Integer)
    LostUserId = db.Column(db.Text)
    FoundUserId = db.Column(db.Text)
    similarity = db.Column(db.Integer)

    def __init__(self, LostId, FoundId, LostUserId, FoundUserId, similarity):
        self.LostId = LostId
        self.FoundId = FoundId
        self.LostUserId = LostUserId
        self.FoundUserId = FoundUserId
        self.similarity = similarity


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    RelatedReportId = db.Column(db.Integer)
    RelatedId = db.Column(db.Integer)
    Notification = db.Column(db.Text)
    UserId = db.Column(db.Text)
    IsReaded = db.Column(db.Boolean)
    Date = db.Column(db.Text)

    def __init__(self, RelatedReportId,  Notification, RelatedId, UserId, IsReaded, Date):
        self.RelatedReportId = RelatedReportId
        self.Notification = Notification
        self.UserId = UserId
        self.IsReaded = IsReaded
        self.RelatedId = RelatedId
        self.Date = Date


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    ReportId = db.Column(db.Integer, )

    def __init__(self, longitude, latitude, ReportId):
        self.latitude = latitude
        self.longitude = longitude
        self.ReportId = ReportId


# Product Schema


class ProductSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'ReportType',
                  'mimetype', 'imageEncode', 'imageURL', 'UserId', 'ReportId')


product_schema = ProductSchema(strict=True)
products_schema = ProductSchema(many=True, strict=True)


# RelatedReport Schema

class RelatedReportSchema(ma.Schema):
    class Meta:
        fields = ('LostId', 'FoundId', 'LostUserId',
                  'FoundUserId', 'similarity')


RelatedReport_Schema = RelatedReportSchema(strict=True)
RelatedReports_Schema = RelatedReportSchema(many=True, strict=True)

# Notification Schema


class NotificationSchema(ma.Schema):
    class Meta:
        fields = ('RelatedReportId', 'Notification',
                  'UserId', 'IsReaded', 'RelatedId', 'Date')


Notification_Schema = NotificationSchema(strict=True)
Notifications_Schema = NotificationSchema(many=True, strict=True)

# Loaction Schema


class LoactionnSchema(ma.Schema):
    class Meta:
        fields = ('longitude', 'latitude', 'ReportId')


Loaction_Schema = LoactionnSchema(strict=True)
Loactions_Schema = LoactionnSchema(many=True, strict=True)


# relatedReport

def RelatedReportData(id):
    LostRelatedReports = db.session.query(RelatedReport).filter(
        RelatedReport.LostUserId == id).all()
    FoundRelatedReports = db.session.query(RelatedReport).filter(
        RelatedReport.FoundUserId == id).all()

    data = []
    for r in LostRelatedReports:

        data.append({'id': r.id, 'LostId': r.LostId, 'FoundId': r.FoundId,
                    'LostUserId': r.LostUserId, 'FoundUserId': r.FoundUserId})
    for r in FoundRelatedReports:

        if len(data) == 0:
            data.append({'id': r.id, 'LostId': r.LostId, 'FoundId': r.FoundId,
                         'LostUserId': r.LostUserId, 'FoundUserId': r.FoundUserId})
        else:
            for d in data:
                if d['LostId'] == r.LostId and d['FoundId'] == r.FoundId:
                    continue
                data.append({'id': r.id, 'LostId': r.LostId, 'FoundId': r.FoundId,
                             'LostUserId': r.LostUserId, 'FoundUserId': r.FoundUserId})
                break

    return data


def GetRelatedReportById(id):
    try:

        data = db.session.query(RelatedReport).filter(
            RelatedReport.id == id).all()

        return data
    except:

        return None


def AddNotification(id):
    data = RelatedReportData(id)

    for d in data:

        if(d['LostUserId'] == id):
            try:
                notifications = Notification.query.filter_by(
                    UserId=id, RelatedReportId=d['FoundId'], RelatedId=d['id']).one()
            except:

                notify = "We may find report about the person you are looking for"
                notification = Notification(
                    RelatedReportId=d['FoundId'], RelatedId=d['id'], Notification=notify, UserId=id, IsReaded=False, Date=date.today().strftime('%d %B,%Y'))
                db.session.add(notification)

                notify = "We may find report about the person you found"
                notification = Notification(
                    RelatedReportId=d['LostId'], RelatedId=d['id'], Notification=notify, UserId=d['FoundUserId'], IsReaded=False, Date=date.today().strftime('%d %B,%Y'))
                db.session.add(notification)
                db.session.commit()

        else:

            try:

                notifications = Notification.query.filter_by(
                    UserId=id, RelatedReportId=d['LostId'], RelatedId=d['id']).one()
                print(d)
            except:

                notify = "We may find report about the person you are looking for"
                notification = Notification(
                    RelatedReportId=d['FoundId'], RelatedId=d['id'], Notification=notify, UserId=d['LostUserId'], IsReaded=False, Date=date.today().strftime('%d %B,%Y'))
                db.session.add(notification)

                notify = "We may find report about the person you found"
                notification2 = Notification(
                    RelatedReportId=d['LostId'], RelatedId=d['id'], Notification=notify, UserId=id, IsReaded=False, Date=date.today().strftime('%d %B,%Y'))
                db.session.add(notification2)
                db.session.commit()


def imagesRelates(id):

    img = Images.query.filter_by(id=id).first()

    if(img.ReportType == 0):
        there = 0
        images = Images.query.filter_by(ReportType=1).all()
        for image in images:
            print(img)
            list1 = ast.literal_eval(img.imageEncode)
            list2 = ast.literal_eval(image.imageEncode)
            list1 = np.array(list1)
            resultCompare = compare(list1, list2)

            if(resultCompare == True):
                there = there+1
                relatedReport = RelatedReport(
                    LostId=img.ReportId, FoundId=image.ReportId, LostUserId=img.UserId, FoundUserId=image.UserId, similarity=100)
                db.session.add(relatedReport)
                db.session.commit()
            else:
                similarity1 = float(imageSimilarity(
                    img.imageURL, image.imageURL))
                print(similarity1)
                similarity2 = float(imageSimilarity(
                    image.imageURL, img.imageURL))
                print(similarity2)

                if(similarity1 > similarity2):

                    similarity1 = similarity1 * 100
                    relatedReport = RelatedReport(
                        FoundId=image.ReportId, LostId=img.ReportId, FoundUserId=image.UserId, LostUserId=img.UserId, similarity=similarity1)
                    db.session.add(relatedReport)

                    db.session.commit()
                else:

                    similarity2 = similarity2 * 100
                    relatedReport = RelatedReport(
                        FoundId=image.ReportId, LostId=img.ReportId, FoundUserId=image.UserId, LostUserId=img.UserId, similarity=similarity2)
                    db.session.add(relatedReport)
                    db.session.commit()

        return there
    else:

        images = Images.query.filter_by(ReportType=0).all()
        print("in")
        there = 0
        for image in images:
            list1 = ast.literal_eval(img.imageEncode)

            list2 = ast.literal_eval(image.imageEncode)
            list1 = np.array(list1)
            resultCompare = compare(list1, list2)

            if(resultCompare == True):
                there = there+1
                relatedReport = RelatedReport(
                    LostId=image.ReportId, FoundId=img.ReportId, LostUserId=image.UserId, FoundUserId=img.UserId, similarity=100)
                db.session.add(relatedReport)
                db.session.commit()
            else:
                similarity1 = float(imageSimilarity(
                    img.imageURL, image.imageURL))

                similarity2 = float(imageSimilarity(
                    image.imageURL, img.imageURL))

                if(similarity1 > similarity2):

                    similarity1 = similarity1 * 100
                    relatedReport = RelatedReport(
                        LostId=image.ReportId, FoundId=img.ReportId, LostUserId=image.UserId, FoundUserId=img.UserId, similarity=similarity1)
                    db.session.add(relatedReport)
                    db.session.commit()
                    print(similarity1)
                else:
                    similarity2 = similarity2 * 100
                    relatedReport = RelatedReport(
                        LostId=image.ReportId, FoundId=img.ReportId, LostUserId=image.UserId, FoundUserId=img.UserId, similarity=similarity2)
                    db.session.add(relatedReport)
                    db.session.commit()
                    print(similarity2)
        return there

    images = Images.query.all()
    list1 = ast.literal_eval(img[0].imageEncode)
    list2 = ast.literal_eval(img[1].imageEncode)

    list1 = np.array(list1)

    resultCompare = compare(list1, list2)
    if(resultCompare == True):
        relatedReport = RelatedReport(LostId=img[0].id, FoundId=img[1].id)
        db.session.add(relatedReport)
        db.session.commit()

    result = products_schema.dump(img)
    return jsonify(result)


@ app.route('/GetNotification/<string:id>', methods=['GET'])
def GetNotification(id):
    data = []
    notifications = Notification.query.filter_by(UserId=id).all()
    Notification.query.filter_by(UserId=id).update(
        {Notification.IsReaded: True})
    db.session.commit()
    relatedReports = []
    counts = []
    for notify in notifications:
        status = False

        for count in counts:
            if(notify.RelatedReportId == count['id']):
                count['count'] += 1
                status = True
        if(not status):
            counts.append({"id": notify.RelatedReportId, "count": 1})

    for count in counts:

        Lostrelated = RelatedReport.query.filter_by(
            FoundId=count['id'], LostUserId=id).all()
        Foundrelated = RelatedReport.query.filter_by(
            LostId=count['id'], FoundUserId=id).all()

        if(len(Lostrelated) == 0):
            for related in Foundrelated:
                relatedReports.append(related)
        else:
            for related in Lostrelated:
                relatedReports.append(related)
    reportId = []
    index = 0
    notifyId = 0
    allReportID = [{}]
    for notification in notifications:
        print("one")
        if(notifyId != notification.RelatedReportId):
            reportId = []
            index = 0

        for replatedReport in relatedReports:
            similarity = 0
            notifyId = notification.RelatedReportId

            if(replatedReport.LostId == notification.RelatedReportId):
                try:

                    allReportID.index(
                        {replatedReport.FoundId: notification.RelatedReportId})

                except:
                    print(replatedReport.similarity)
                    similarity = replatedReport.similarity
                    reportId.append(replatedReport.FoundId)
                    allReportID.append(
                        {replatedReport.FoundId: notification.RelatedReportId})
                    index = index + 1

                    break

            elif(replatedReport.FoundId == notification.RelatedReportId):
                try:

                    allReportID.index(
                        {replatedReport.LostId: notification.RelatedReportId})
                except:
                    similarity = replatedReport.similarity
                    reportId.append(replatedReport.LostId)
                    allReportID.append(
                        {replatedReport.LostId: notification.RelatedReportId})
                    index = index + 1
                    break

        try:
            print("in")
            print(similarity)
            data.append({'id': notification.id, 'reportid': notification.RelatedReportId, "relatedReportId": reportId[index-1], 'notification': notification.Notification,
                         "date": notification.Date, "similarity": similarity})

        except:
            continue
        notification.IsReaded = True

    if(data == None):
        return jsonify({"empty"}), 400
    print(data)
    return jsonify(data), 200


@ app.route('/GetNotificationCount/<string:id>', methods=['GET'])
def GetNotificationCount(id):
    relatedReports = []
    data = []
    notifications = Notification.query.filter_by(
        UserId=id, IsReaded=False).all()
    print(len(notifications))
    counts = []
    for notify in notifications:
        status = False

        for count in counts:
            if(notify.RelatedReportId == count['id']):
                count['count'] += 1
                status = True
        if(not status):
            counts.append({"id": notify.RelatedReportId, "count": 1})

    for count in counts:

        Lostrelated = RelatedReport.query.filter_by(
            FoundId=count['id'], LostUserId=id).all()
        Foundrelated = RelatedReport.query.filter_by(
            LostId=count['id'], FoundUserId=id).all()

        if(len(Lostrelated) == 0):
            for related in Foundrelated:
                relatedReports.append(related)
        else:
            for related in Lostrelated:
                relatedReports.append(related)
    reportList = []

    for notification in notifications:
        reportId = 0
        for replatedReport in relatedReports:
            if(replatedReport.id == notification.RelatedId):

                if(replatedReport.LostId == notification.RelatedReportId):
                    try:

                        reportList.index(replatedReport.FoundId)
                    except:
                        reportId = replatedReport.FoundId
                        reportList.append(reportId)
                else:
                    try:

                        reportList.index(replatedReport.LostId)
                    except:
                        reportId = replatedReport.LostId
                        reportList.append(reportId)

            if(reportId == 0):
                continue
            data.append({'id': notification.id, 'reportid': notification.RelatedReportId, "relatedReportId": reportId, 'notification': notification.Notification,
                         "date": notification.Date})
    counts = []

    for d in data:
        status = False

        for count in counts:
            if(d['relatedReportId'] == count['id']):
                count['count'] += 1
                status = True
        if(not status):
            print(d)
            counts.append({"id": d['relatedReportId'], "count": 1})
    print(counts)
    if(len(notifications) == 0):
        return jsonify(0), 400
    return jsonify(len(counts)), 200


@ app.route('/GetRelatedReport/<string:id>', methods=['GET'])
def GetRelatedReport(id):

    data = GetRelatedReportById(id)

    data = {'LostId': data[0].LostId, 'FoundId': data[0].FoundId}
    return jsonify(data), 201


@ app.route('/upload2', methods=['POST'])
def Upload2():

    pic = request.files['image']
    image = Image.open(pic)
    ReportType = request.form['reportType']
    UserId = request.form['UserId']
    fileName = secure_filename(pic.filename)
    mimetype = pic.mimetype
    imageEncode = encoding(image)
    imageEncode = imageEncode.tolist()

    if(ReportType == '0'):
        image.save(f"images\Lost\{fileName}")
        imageURl = f"images\Lost\{fileName}"
    elif(ReportType == '1'):
        image.save(f"images\Found\{fileName}")
        imageURl = f"images\Found\{fileName}"
    else:
        dictToReturn = {"valid": f'{False}'}

        return jsonify(dictToReturn), 400

    img = Images(name=fileName, ReportType=ReportType,
                 imageEncode=f'{imageEncode}', mimetype=mimetype, imageURL=imageURl, UserId=UserId.replace('"', ''), ReportId=int(request.form['reportId']))
    db.session.add(img)
    db.session.commit()
    executor.submit(imagesRelates(img.id))
    executor.submit(AddNotification(UserId.replace('"', '')))
    dictToReturn = {"valid": f'{img.id}'}
    return jsonify(img.id), 201


@ app.route('/CheckValidation', methods=['POST'])
def CheckValidation():
    pic = request.files['image']
    image = Image.open(pic)
    valid = checkValidation(image)
    if(valid == True):

        return jsonify(valid), 201
    else:

        return jsonify(valid), 400


# Add Report Location
@ app.route('/AddLoaction', methods=['POST'])
def AddLoaction():
    country = request.form['country']
    city = request.form['city']
    district = request.form['district']
    Lan_Latt = getLoaction(country, city, district)
    location = Location(Lan_Latt[0], Lan_Latt[1], request.form['ReportId'])
    db.session.add(location)
    db.session.commit()
    return jsonify(True), 200


@ app.route('/GetLoaction', methods=['GET'])
def GetLoaction():
    Loactions = Location.query.all()
    LoactionList = []
    longitudes = []
    latitudes = []
    longitudes.append(0)
    latitudes.append(0)
    for loaction in Loactions:
        if (loaction.longitude not in longitudes and loaction.latitude not in latitudes):

            LoactionList.append(
                {"longitude": loaction.longitude, "latitude": loaction.latitude})
            latitudes.append(loaction.latitude)
            longitudes.append(loaction.longitude)

    return jsonify(LoactionList), 200


@ app.route("/Delete/<string:id>", methods=['DELETE'])
def Delete(id):

    Images.query.filter_by(
        ReportId=id).delete()
    RelatedReport.query.filter_by(
        LostId=id).delete()

    RelatedReport.query.filter_by(
        FoundId=id).delete()

    Notification.query.filter_by(
        RelatedReportId=id).delete()
    db.session.commit()
    return jsonify("done"), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000, host="localhost")
