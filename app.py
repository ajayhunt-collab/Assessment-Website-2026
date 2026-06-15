from flask import Flask, g, render_template, request, flash, session, redirect, url_for 
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "database.db"

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

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

@app.route('/signup', methods=["GET","POST"])
def signup():
    #if the user posts from the signup page
    if request.method == "POST":
        #add the new username and hashed password to the database
        username = request.form['username']
        password = request.form['password']
        #hash it with the cool secutiry function
        hashed_password = generate_password_hash(password)
        #write it as a new user to the database
        sql = "INSERT INTO User (Username,Password) VALUES (?,?)"
        write_db(sql,(username,hashed_password))
        #message flashes exist in the base.html template and give user feedback
        flash("Sign Up Successful")
    return render_template('signup.html')

@app.route('/login', methods=["GET","POST"])
def login():
    #if the user posts a username and password
    if request.method == "POST":
        #get the username and password
        username = request.form['username']
        password = request.form['password']
        #try to find this user in the database- note- just keepin' it simple so usernames must be unique
        sql = "SELECT * FROM User WHERE Username = ?"
        user = query_db(sql,(username,),True)
        if user:
            #we got a user!!
            #check password matches-
            if check_password_hash(user[2],password):
                #we are logged in successfully
                #Store the username in the session
                session['User'] = user
                flash("Logged in successfully")
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
    #render this template regardles of get/post
    return render_template('login.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port= 5000, debug = True) 