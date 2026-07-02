from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'MY NAME is Pradeep!'


@app.route("/about")
def about():
    return "I am a software engineer with a passion for developing innovative programs that expedite the efficiency and effectiveness of organizational success. I am skilled in technology and writing code to create systems that are reliable and user-friendly. I am also a quick learner and can adapt to new technologies as they emerge."



@app.route('/count')
def count():
    my_list = ['apple', 'banana', 'cherry', 'date', 'elderberry']
    return f'The number of items in the list is: {len(my_list)}'

@app.route('/greet/<name>')
def greet(name):
    return f'Hello, {name}! Welcome to my Flask app.'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
