from flask import Flask, render_template, redirect, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# User table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(200))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname).first()
        if user and check_password_hash(user.password, pwd):
            session['username'] = uname
            return redirect('/chat')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if not User.query.filter_by(username=uname).first():
            hashed = generate_password_hash(pwd)
            db.session.add(User(username=uname, password=hashed))
            db.session.commit()
            return redirect('/')
    return render_template('register.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect('/')
    return render_template('chat.html', username=session['username'])

@socketio.on('join')
def handle_join(data):
    join_room(data['room'])
    emit('status', {'msg': f"{data['username']} joined {data['room']}."}, room=data['room'])

@socketio.on('message')
def handle_message(data):
    emit('message', data, room=data['room'])

@socketio.on('leave')
def handle_leave(data):
    leave_room(data['room'])
    emit('status', {'msg': f"{data['username']} left {data['room']}."}, room=data['room'])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
