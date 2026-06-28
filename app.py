from flask import Flask, g, render_template, request, flash, session, redirect, url_for 
import sqlite3
import os

from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db') 

app = Flask(__name__)

app.config['SECRET_KEY'] = "MyReallySecretKey"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def write_db(query,args=(),one=False):
    '''connect and query- will retun one item if one=true and can accept arguments as tuple'''
    db = get_db()
    cur = db.cursor()
    cur.execute(query,args)
    rv = cur.fetchall() 
    db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/signup', methods=["GET","POST"])
def signup():
    #if the user posts from the signup page
    if request.method == "POST":
        #add the new username and hashed password to the database
        username = request.form['email']
        password = request.form['password']
        #hash it with the cool secutiry function
        hashed_password = generate_password_hash(password)
        #write it as a new user to the database
        sql = "INSERT INTO Students (Email,Password) VALUES (?,?)"
        write_db(sql,(username,hashed_password))
        #message flashes exist in the base.html template and give user feedback
        flash("Sign Up Successful")
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=["GET","POST"])
def login():
    #if the user posts a username and password
    if request.method == "POST":
        #get the username and password
        username = request.form['email']
        password = request.form['password']
        #try to find this user in the database- note- just keepin' it simple so usernames must be unique
        sql = "SELECT * FROM Students WHERE Email = ?"
        user = query_db(sql,(username,),True)
        if user:
            #check password matches-
            if check_password_hash(['Password'],password):
                #we are logged in successfully
                #Store the username in the session
                session['Students'] = user['Email']
                flash("Logged in successfully")
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
    #render this template regardles of get/post
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('User', None)
    flash("You have been logged out")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port= 5000, debug = True) 