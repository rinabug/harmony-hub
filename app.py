from flask import Flask, render_template, url_for, redirect, session, flash, jsonify

app = Flask(__name__)

@app.route('/')
def start_page():
    return render_template('start-page.html')

@app.route('/login')
def login():
    return render_template('login.html')  

@app.route('/signup')
def signup():
    return render_template('signup.html')  

@app.route('/index')
def index():
    return render_template('index.html')  

@app.route('/profile')
def profile():
    return render_template('profile.html')  

@app.route('/discover')
def discover():
    return render_template('discover.html') 

@app.route('/collab')
def collab():
    return render_template('collab.html')  

@app.route('/logout')
def logout():
    return redirect(url_for('start_page'))

if __name__ == '__main__':
    app.run(debug=True)