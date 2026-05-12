from flask import Flask, g, render_template, request, flash, session, redirect, url_for 
import sqlite3

from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "database.db"

app = Flask(__name__)

@app.route('/')
def home():
    #home page
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True) 