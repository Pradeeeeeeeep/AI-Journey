from flask import Flask, render_template,request

app = Flask(__name__)

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        return f"Hello, {username}!"
    return render_template('login.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)