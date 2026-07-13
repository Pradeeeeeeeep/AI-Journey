from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('login.html')

@app.route('/submit', methods = ['POST'])
def submit():
    id = request.form.get('id')
    passw = request.form.get('pass')

    if id == 'COL/2026/0111' and passw == '1001' :
        render_template('dashboard.html')
