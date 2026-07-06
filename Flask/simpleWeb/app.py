from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/submit', methods=['POST'])
def submit():
    mail = request.form.get('mail')
    password = request.form.get('password')
    
    if mail == 'admin@mail.com' and password == 'admin':
        return render_template('welcome.html', mail=mail)
    else:
        return 'Invalid credentials. Please try again.'