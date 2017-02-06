'''{points: [{lon: float, lan: float, radius: float}, ...]}'''

from flask import Flask, render_template, make_response, request, session, redirect, url_for, flash
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy as sql
from sqlalchemy.orm import sessionmaker
from Adafruit_BME280 import *
from hurry.filesize import size
#from flask_login import LoginManager, UserMixin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, VARCHAR, engine, create_engine
from werkzeug.security import generate_password_hash, check_password_hash
import psutil
import collections

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://pi:raspi@localhost/web_service'
#login_manager = LoginManager()
app.secret_key = 'fdsjgghasghadasdasda'
api = Api(app)
#login_manager.init_app(app)
#db = sql(app)
db = 'mysql://pi:raspi@localhost/web_service' 
Base = declarative_base()

class User(object):
    def __init__(self, username, password):
        self.username = username
        #self.password = self.set_password(passwd)
        self.set_password(password)
        self.email = '{}@domain.com'.format(username)
    
    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR)
    password = Column(VARCHAR)
    email = Column(VARCHAR)

def connect_to_db():
    engine = create_engine(db) 
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

x = 12.12
y = 23.23
z = 34.34

#class User(UserMixin):
#    def __init__(self, username, password):
#        self.id = username
#        self.password = password

@app.route("/")
def index():
    if 'username' in session:
        user_name = session['username']
        return render_template('projects.html', username = user_name)
    else:
        return render_template('index.html')

def valid_login(user_name, passwd, session):
    result = session.query(Users).filter(Users.username == user_name).one()
    if check_password_hash(result.password, passwd):
        return True
    else:
        return False

@app.route('/login', methods = ['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'],
                       request.form['passwd'], connect_to_db()):
            session['username'] = request.form['username']
            resp = make_response(render_template('projects.html', username = session['username']))
            return resp
        else:
            error = 'Invalid username/password'
    return render_template('index.html', error = error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/projects')
def projects():
    if 'username' in session:
        user_name = session['username']
        return render_template('projects.html', username = user_name)
    else:
        return render_template('index.html')

@app.route('/system')
def system():
    if 'username' in session:
        cpu_stats = collections.OrderedDict()
        mem_stats = collections.OrderedDict()
        cpu = psutil.cpu_percent(percpu=True)
        i = 1
        for item in cpu:
            cpu_stats['core{}'.format(i)] = item
            i += 1
        mem = psutil.virtual_memory()
        mem_stats['total'] = size(mem.total)
        mem_stats['available'] = size(mem.available)
        mem_stats['percent'] = mem.percent
        mem_stats['used'] = size(mem.used)
        mem_stats['free'] = size(mem.free)
        return render_template('system.html', result = cpu_stats, mem_stats = mem_stats)
    else:
        return redirect(url_for('index'))

#@app.route("/sensor")
def sensor_data():
    if 'username' in session:
        sensor = BME280(mode=BME280_OSAMPLE_8)
        degrees = sensor.read_temperature()
        pascals = sensor.read_pressure()
        hectopascals = pascals / 100
        humidity = sensor.read_humidity()
        result = {
                 'temperature': degrees,
                 'pressure': hectopascals,
                 'humidity': humidity
                 }
        return result
    else:
        return redirect(url_for('index'))
    #return render_template('result.html', result = result)

class Sensor_data(Resource):
    def __init__(self):
        pass
    def get(self):
        sensor = BME280(mode=BME280_OSAMPLE_8)
        degrees = sensor.read_temperature()
        pascals = sensor.read_pressure()
        hectopascals = pascals / 100
        humidity = sensor.read_humidity()
        result = {
                'temperature': round(degrees, 2), 
                'pressure': round(hectopascals, 3), 
                'humidity': round(humidity, 2)
                }
        #headers = {'Content-Type': 'text/html'}
        return make_response(render_template("result.html", result = result))#, 200, headers)

@app.route('/new', methods = ['GET', 'POST'])
def new_user():
    if 'username' in session:
        db_session = connect_to_db()
        if request.method == 'POST':
            if not request.form['name'] or not request.form['password']:
                flash('Please enter all the fields', 'error')
            else:
                user = User(request.form['name'], request.form['password'])
                user_db = Users(username=user.username, password=user.pw_hash, email=user.email)
                db_session.add(user_db)
                db_session.commit()
                flash('User was sucessfully added')
                #return redirect(url_for('show_users')
                return 'ok'
        return render_template('new.html')
    else:
        return redirect(url_for('index'))

#@app.route("/points")
#def points():
#    x = 12.12
#    y = 23.23
#    z = 34.34
#    return "{'points': [{'lon': x, 'lan': y, 'radius': z}]}"

class Points(Resource):
    def get(self):
        return {'points': [{'lon': x, 'lan': y, 'radius': z}]}

api.add_resource(Points, '/points')
api.add_resource(Sensor_data, '/sensor')

if __name__ == "__main__":
    app.run('192.168.0.24', debug = True)


