from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

# @app.route('/<name>')
# def home(name):
#     return render_template('index.html', name = name)



@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/dashboard/<name>/<age>/<city>/<course>')
def dashboard(name, age, city, course):
    skills = ['Python', 'Flask', 'HTML', 'CSS', 'JavaScript']
    eligible = course == 'AIML' and age >= '18'
    return render_template('dashboard.html', name=name, age=age, city=city, course=course, skills=skills, eligible=eligible)



@app.route('/youtube/<id>')
def youtube(id):
    return render_template('youtbePlayer.html', id=id)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)