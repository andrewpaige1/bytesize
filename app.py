from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt
import string 
import random
from flask_socketio import SocketIO, join_room, emit, send
from bson.json_util import loads, dumps
import json


app = Flask('app')
app.config.from_pyfile('config.cfg')
mongo = PyMongo(app)
ROOMS = {}
socketio = SocketIO(app)

@app.route('/')
def index():
    if 'username' in session:
        posts = mongo.db.room
        all_docs = posts.find({})
        all_docs_string = dumps(all_docs)
        all_docs2 = json.loads(all_docs_string)
        return render_template('home.html', rooms=all_docs2, user=session['username'])
    return render_template('index.html')


@app.route('/members/<room_id>')
def members(room_id):
    if 'username' in session:
        posts = mongo.db.room
        all_docs = posts.find_one({'id': room_id})
        all_docs_string = dumps(all_docs)
        all_docs2 = json.loads(all_docs_string)
        return render_template('members.html', members=all_docs2['members'])

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    users = mongo.db.users
    login_user = users.find_one({'name' : request.form['username']})

    if login_user:
        if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password']) == login_user['password']:
            session['username'] = request.form['username']
            return redirect(url_for('index'))

    return redirect(url_for('index'))



@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name' : request.form['username']})

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name' : request.form['username'], 'password' : hashpass})
            session['username'] = request.form['username']
            return redirect(url_for('index'))
        
        return render_template('register.html', message="This name is already taken!")

    return render_template('register.html', message="")



@app.route('/reducer')
def byte():
    return render_template('reducer.html')


@socketio.on('createRoom')
def create_room():
    room_collection = mongo.db.room
    id = room_collection.find_one({'id': request.form['roomCode']})
    room = id
    ROOMS[room] = id
    join_room(room)
    emit('join_room', {'room': room})


@socketio.on('joinRoom')
def on_join(data):
    """Join a game lobby"""
    # username = data['username']
    room = data['room']
    if room in ROOMS:
        # add player and rebroadcast game object
        # rooms[room].add_player(username)
        join_room(room)
        send(ROOMS[room].to_json(), room=room)
    else:
        emit('error', {'error': 'Unable to join room. Room does not exist.'})

@app.route('/group', methods=['GET', 'POST'])
def group():
    return render_template('groupReducer.html', id=request.args['roomCode'])

@app.route('/groupReducer', methods=['GET', 'POST'])
def group_reducer():
    def reduceCalories(calories):
        portion = 0;
        subCal = 0
        holding = ""
    
        if calories <= 700:
          portion = 0

    
        while calories >= 700:
            calories -= 1;
            portion += 1;
          
        
        subCal -= 1
        if portion <= 2500 and portion >= 1401:
          holding = "You " + " should have a quarter of the meal"
      
        elif portion <= 1400 and portion >= 801:
            holding = "You " + " should have a quarter of the meal"
      
        
        elif portion <= 800 and portion >= 401:
            holding = "You " + " should have half of the meal"
      
        elif portion <= 400 and portion >= 101:
           holding = "You " + " should have a little more than half the meal";
      
        elif portion <= 100 and portion >= 0:
          holding = "You " + " can have the full meal";
      
        else:
          holding = "The meal is too big"
      
        return holding


    if request.method == 'POST':
        room_collection = mongo.db.room
        calories = request.form['calories']
        if calories.isnumeric():
            calories = int(calories)
        else:
            return render_template('groupReducer.html', message="please enter a valid number")
        meal_name = request.form['mealName']
        name = session['username']
        result = reduceCalories(calories)
        room_collection.update_one({"id": request.args['id']}, {'$push': {'members': {'name': name, 'mealName': meal_name, 'rec': result}}})

        return redirect(url_for('index'))
    


@app.route('/join')
def join():
#    room = 
    return render_template('join.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        id = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 5))
        room = mongo.db.room
        room.insert_one({'creator': session['username'], 'id': id, 'members': []})
        return render_template('create.html', id=id)
    return render_template('create.html', id="")

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)