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

def write_db(query, args=(), one=False):
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    rv = cur.fetchall() 
    db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# --- GLOBAL GATEKEEPER SECURITY WALL ---
@app.before_request
def lock_down_routes():
    # 1. Always let CSS/static design files through so the sign-up page looks right
    if request.endpoint == 'static':
        return

    # 2. Allow access to signup and login paths explicitly
    allowed_routes = ['signup', 'login']
    if request.endpoint in allowed_routes:
        return

    # 3. If the user is NOT logged into the session, intercept and force them to sign up
    if not session.get('Students'):
        flash("Please sign up or login to access the portal.")
        return redirect(url_for('signup'))


# --- ROUTES AND ENDPOINTS ---

@app.route('/')
# --- UPDATE THESE TWO ROUTES AT THE TOP OF YOUR ENDPOINTS SECTION ---
def index():
    # 1. Force the root page to instantly evaluate the login wall
    if not session.get('Students'):
        return redirect(url_for('signup'))
    return redirect(url_for('home'))


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['email']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        sql = "INSERT INTO Students (Email,Password) VALUES (?,?)"
        write_db(sql, (username, hashed_password))
        
        # Log them into the session
        session['Students'] = username
        flash("Sign Up Successful!")
        return redirect(url_for('home'))
        
    # If authenticated, don't show the sign-up form, push them home
    if session.get('Students'):
        return redirect(url_for('home'))
        
    return render_template('signup.html')

@app.route('/home')
def home():
    # Pulls sports cards out of the table using your column
    sql = "SELECT * FROM Sports"
    all_sports = query_db(sql)
    return render_template('home.html', sports=all_sports)


@app.route('/sports')
def sports():
    # Fetches all sports listed for the secondary grid sub-page if needed
    sql = "SELECT * FROM Sports"
    all_sports = query_db(sql)
    return render_template('sports.html', sports=all_sports)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['email']
        password = request.form['password']
        
        sql = "SELECT * FROM Students WHERE Email = ?"
        user = query_db(sql, (username,), True)
        
        if user:
            if check_password_hash(user['Password'], password):
                session['Students'] = user['Email']
                flash("Logged in successfully")
                return redirect(url_for('home'))
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('Students', None)
    flash("You have been logged out successfully")
    return redirect(url_for('signup'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
