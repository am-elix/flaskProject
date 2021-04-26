import os
import sys
from datetime import datetime

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def getMap(coords, scale, viewMap="map", mark=""):
    params = {"ll": ",".join(coords),
              "l": viewMap,
              "z": scale,
              "pt": mark
              }
    if mark != "":
        params["pt"] = ",".join(coords) + "," + mark
    url = "https://static-maps.yandex.ru/1.x/"
    response = requests.get(url, params=params)
    if not response:
        print("Ошибка выполнения запроса:")
        print(f"http://static-maps.yandex.ru/1.x/?ll={coords[0]},{coords[1]}&spn=0.001,0.001&l=map")
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)
    return response


def getObjectCoords(name):
    APIKEY = "40d1649f-0493-4b70-98ba-98533de7710b"
    params = {"apikey": APIKEY,
              "geocode": name,
              "format": "json"}
    url = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(url, params=params)
    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        toponym_address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
        toponym_coodrinates = toponym["Point"]["pos"]
        return toponym_coodrinates.split()


class UserOnWeb:
    loginnedUser = None

    def changeUser(self, name):
        self.loginnedUser = name

    def returnUserName(self):
        return self.loginnedUser


class UsersRequests(db.Model):
    requestId = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    startOfReservation = db.Column(db.String, nullable=False)
    nightsAmount = db.Column(db.Integer, nullable=False)
    guestsAmount = db.Column(db.Integer, nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('user.id'))
    dateRequest = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<Article %r>' % self.requestId


class HotelsBase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    hotelName = db.Column(db.String, nullable=False)
    imgOfHotel = db.Column(db.String, nullable=False)
    imgOfHotel1 = db.Column(db.String, nullable=True)
    imgOfHotel2 = db.Column(db.String, nullable=True)
    imgOfHotel3 = db.Column(db.String, nullable=True)
    imgOfHotel4 = db.Column(db.String, nullable=True)
    shortInfo = db.Column(db.String, nullable=False)
    userAccessName = db.Column(db.String, db.ForeignKey('user.userName'))

    def __repr__(self):
        return '<Article %r>' % self.id


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userTelephone = db.Column(db.String(12), nullable=False)
    userEmail = db.Column(db.String(100), nullable=False)
    userFullName = userName = db.Column(db.String(100), nullable=False)
    userName = db.Column(db.String(30), nullable=False)
    userPassword = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Article %r>' % self.id


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        if UserOnWeb.returnUserName(UserOnWeb):
            # action="https://jsonplaceholder.typicode.com/posts" autocomplete="on"
            city = request.form['Город']
            category = request.form['Категория номера']
            startOfReservation = request.form['Дата заселения']
            nightsAmount = request.form['Количество ночей']
            guestsAmount = request.form['Количество гостей']

            timeNow = datetime.now().date()
            startdate = datetime.strptime(startOfReservation, "%Y-%m-%d").date()
            if startdate < timeNow:
                return render_template('hotel.html', applicationAcceptance='Вы выбрали некорректную дату')

            userName = UserOnWeb.loginnedUser

            userClass = None
            usersInfo = User.query.order_by(User.date.desc()).all()
            for elem in usersInfo:
                if elem.userName == userName:
                    userClass = elem

            try:
                userRequest = UsersRequests(city=city, category=category, startOfReservation=startOfReservation,
                                            nightsAmount=int(nightsAmount), guestsAmount=int(guestsAmount),
                                            userId=int(userClass.id))

                db.session.add(userRequest)
                db.session.commit()

                return render_template('hotel.html', applicationAcceptance='Заявка была успешно принята',
                                       user=UserOnWeb.loginnedUser)
            except:
                print('При регистрации в аккаунт произошла ошибка')
        else:
            return render_template('hotel.html',
                                   applicationAcceptance='Перед отправкой заявки вам надо войти в аккаунт')

    if UserOnWeb.returnUserName(UserOnWeb):
        return render_template("hotel.html", user=UserOnWeb.loginnedUser)
    return render_template("hotel.html")


@app.route('/usersRequests')
def allUsersRequests():
    res = db.session.query(User, UsersRequests).join(UsersRequests, User.id == UsersRequests.userId).all()
    return render_template("allUsersRequests.html", requestsInfo=res)


@app.route('/users')
def users():
    usersInfo = User.query.order_by(User.date.desc()).all()
    return render_template("users.html", usersInfo=usersInfo)


@app.route('/personalUserArea')
def personalUserArea():
    res = db.session.query(User, UsersRequests).join(UsersRequests, User.id == UsersRequests.userId).all()
    userReq = False
    for elem in res:
        if elem.User.userName == UserOnWeb.loginnedUser:
            userReq = True
    if userReq:
        return render_template("personalUserArea.html", user=UserOnWeb.loginnedUser, requests=res)
    else:
        return render_template("personalUserArea.html", user=UserOnWeb.loginnedUser, requests=None)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        userName = request.form['userName']
        userPassword = request.form['inputPassword']
        usersInfo = User.query.order_by(User.date.desc()).all()
        for elem in usersInfo:
            if elem.userName == userName and check_password_hash(elem.userPassword, userPassword):
                try:
                    UserOnWeb.loginnedUser = userName
                    return redirect('/')
                except:
                    print('При входе в аккаунт произошла ошибка')
        return render_template("login.html", warning='Вы ввели некорректные данные')
    else:
        return render_template("login.html")


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        userTelephone = request.form['userTelephone']
        userEmail = request.form['userEmail']
        userFullName = request.form['userFullName']
        userName = request.form['userName']
        userPassword = generate_password_hash(request.form['inputPassword'])
        usersInfo = User.query.order_by(User.date.desc()).all()
        for elem in usersInfo:
            if elem.userName == userName:
                return render_template("register.html", warning='Аккаунт с данным именем пользователя уже существует')
        user = User(userTelephone=userTelephone, userEmail=userEmail, userFullName=userFullName, userName=userName,
                    userPassword=userPassword)
        try:
            db.session.add(user)
            db.session.commit()

            UserOnWeb.loginnedUser = userName
            return redirect('/')
        except:
            print('При регистрации в аккаунт произошла ошибка')
    else:
        return render_template("register.html")


@app.route('/logout')
def logout():
    UserOnWeb.loginnedUser = None
    return redirect('/')


@app.route('/userPersonalInfo')
def userPersonalInfo():
    usersInfo = User.query.order_by(User.date.desc()).all()
    return render_template('userPersonalInfo.html', user=UserOnWeb.loginnedUser, info=usersInfo)


@app.route('/<int:id>/del')
def userDel(id):
    user = User.query.get_or_404(id)
    try:
        db.session.delete(user)
        db.session.commit()
        UserOnWeb.loginnedUser = None
        return redirect('/')
    except:
        print('При удалении аккаунта произошла ошибка')
        return redirect('/userPersonalInfo')


@app.route('/<int:id>/update', methods=['POST', 'GET'])
def userUpdate(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.userTelephone = request.form['userTelephone']
        user.userEmail = request.form['userEmail']
        user.userFullName = request.form['userFullName']
        try:
            db.session.commit()
            return redirect('/userPersonalInfo')
        except:
            print('При регистрации в аккаунт произошла ошибка')
    else:
        return render_template('updatePersonalInfo.html', info=user)


@app.route('/createHotelInfo', methods=['POST', 'GET'])
def createHotelInfo():
    if request.method == 'POST':
        city = request.form['city']
        description = request.form['description']
        price = request.form['price']
        hotelName = request.form['hotelName']
        imgOfHotel = request.form['imgOfHotel']
        imgOfHotel1 = request.form['imgOfHotel1']
        imgOfHotel2 = request.form['imgOfHotel2']
        imgOfHotel3 = request.form['imgOfHotel3']
        imgOfHotel4 = request.form['imgOfHotel4']
        shortInfo = request.form['shortInfo']
        userAccessName = UserOnWeb.loginnedUser
        hotel = HotelsBase(city=city, description=description, price=int(price), hotelName=hotelName,
                           imgOfHotel=imgOfHotel,
                           shortInfo=shortInfo, userAccessName=userAccessName, imgOfHotel1=imgOfHotel1,
                           imgOfHotel2=imgOfHotel2,
                           imgOfHotel3=imgOfHotel3, imgOfHotel4=imgOfHotel4)
        try:
            db.session.add(hotel)
            db.session.commit()

            return render_template('createHotelInfo.html', suc='Информация была успешно добавлена')
        except:
            print('При создании информации для отеля произошла ошибка')
    else:
        return render_template('createHotelInfo.html')


@app.route('/allHotels')
def allHotels():
    hotelsInfo = HotelsBase.query.all()
    return render_template('allHotels.html', hotels=hotelsInfo)


@app.route('/allHotels/<int:id>/detail')
def detailedHotels(id):
    hotel = HotelsBase.query.get_or_404(id)
    coords = getObjectCoords(hotel.hotelName)
    response = getMap((coords[0], coords[1]), 15)
    map_file = "static/img-hotel/map.png"
    with open(map_file, "wb") as file:
        file.write(response.content)
    return render_template('detailedHotelPage.html', hotel=hotel, mapFile=map_file)


@app.route('/deleteInfoHotel')
def deleteInfoHotel():
    os.remove("static/img-hotel/map.png")
    return redirect('/')


@app.route('/returnAllHotels')
def returnAllHotels():
    os.remove("static/img-hotel/map.png")
    return redirect('/allHotels')


if __name__ == "__main__":
    app.run(debug=True)
