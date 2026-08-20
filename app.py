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

def setup_and_migrate_database():
    """Automatically builds the master Rosters table and copies data if missing."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Rosters (
            StudentID INTEGER,
            Players TEXT NOT NULL,
            TeamID TEXT NOT NULL,
            PRIMARY KEY (Players, TeamID)
        );
    """)
    
    cursor.execute("SELECT COUNT(*) FROM Rosters;")
    if cursor.fetchone()[0] == 0:
        print("Migrating color squads into the master Rosters table...")
        
        # Safe migration loop from old tables if they exist
        old_tables = ['Senior A', 'Senior Black', 'Senior Blue', 'Senior Green', 'Senior Red', 'Senior Yellow']
        for table in old_tables:
            try:
                cursor.execute(f"INSERT OR IGNORE INTO Rosters (Players, TeamID) SELECT Players, '{table}' FROM [{table}]")
                print(f"Successfully migrated {table} roster!")
            except sqlite3.OperationalError:
                # Skips gracefully if the old table was already dropped or missing
                pass
                

        cursor.execute("""
            UPDATE Rosters
            SET StudentID = (
                SELECT Students.StudentID 
                FROM Students 
                WHERE LOWER(Students.Firstname || ' ' || Students.Surname) = LOWER(Rosters.Players)
            )
            WHERE StudentID IS NULL;
        """)
        
    try:
        cursor.execute("UPDATE Sports SET SportID = 'Basketball' WHERE SportID LIKE 'Baskebtall%';")
        cursor.execute("UPDATE Teams SET SportID = 'Basketball' WHERE SportID LIKE 'Baskebtall%';")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

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


@app.before_request
def lock_down_routes():
    if request.endpoint == 'static':
        return

    allowed_routes = ['signup', 'login']
    if request.endpoint in allowed_routes:
        return

    if not session.get('Students'):
        flash("Please sign up or login to access the portal.")
        return redirect(url_for('signup'))

@app.route('/')
def index():
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
        
        session['Students'] = username
        return redirect(url_for('home'))
        
    if session.get('Students'):
        return redirect(url_for('home'))
        
    return render_template('signup.html')

@app.route('/home')
def home():
    sql = "SELECT * FROM Sports"
    all_sports = query_db(sql)
    return render_template('home.html', sports=all_sports)

@app.route('/sport/<sport_id>')
def sport_teams(sport_id):
    sql = """
        SELECT Teams.TeamID, Teams.SportID, "Teachers/Coaches".Email AS CoachEmail 
        FROM Teams 
        LEFT JOIN "Teachers/Coaches" ON Teams.TeamID = "Teachers/Coaches".TeamID
        WHERE LOWER(Teams.SportID) = LOWER(?)
    """
    selected_teams = query_db(sql, (sport_id,))
    
    return render_template('sports.html', teams=selected_teams, sport_title=sport_id)



@app.route('/sports')
def sports():
    # This query joins your teams with their coaches dynamically
    sql = """
        SELECT Teams.TeamID, Teams.SportID, "Teachers/Coaches".Email AS CoachEmail 
        FROM Teams 
        LEFT JOIN "Teachers/Coaches" ON Teams.TeamID = "Teachers/Coaches".TeamID
    """
    all_teams = query_db(sql)
    return render_template('sports.html', teams=all_teams) # Passing 'teams'

@app.route('/team/<team_id>')
def team_detail(team_id):
    sql = "SELECT * FROM Rosters WHERE TeamID = ?"
    team_players = query_db(sql, (team_id,))
    
    if not team_players:
        flash("No roster found for the selected team.")
        return redirect(url_for('sports'))
    
    return render_template('team_detail.html', team_id=team_id, players=team_players)

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
                return redirect(url_for('home'))
            else:
                flash("Password incorrect")
        else:
            flash("Username does not exist")
            
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('Students', None)
    return redirect(url_for('signup'))


if __name__ == "__main__":
    setup_and_migrate_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
