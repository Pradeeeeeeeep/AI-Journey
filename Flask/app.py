from flask import Flask, render_template

app = Flask(__name__)

@app.route('/<name>')
def home(name):
    return render_template('index.html', name = name)

@app.route('/dashboard/<name>/<age>/<city>/<course>')
def dashboard(name, age, city, course):
    return render_template('dashboard.html', name=name, age=age, city=city, course=course)P/
if __name__ == "__main__":
    app.run(debug=True)