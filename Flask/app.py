from flask import Flask, Response, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'password':
            session['user'] = username;
            return redirect(url_for('success'))
        else:
            return Response('Invalid credentials', mimetype='text/plain')
    return ''' 
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
        '''

@app.route('/success')
def success():
    if 'user' in session:
        return f'''
            <h1>Welcome, {session['user']}!</h1>
            <a href="{url_for('logout')}">Logout</a>
        '''
    else:
        return redirect(url_for('index'))
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))