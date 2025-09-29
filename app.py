from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

app=Flask(__name__)
app.secret_key = 'appsecretkey'
mysql=MySQL()

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ventas'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql.init_app(app)

@app.route('/accesologin', methods=['GET', 'POST'])
def accesologin():
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuario WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        if user:
            session['logueado'] = True
            session['id'] = user['id']
            session['id_rol'] = user['id_rol']

        if user['id_rol'] == 1:
            return render_template('admin.html')
        elif user['id_rol'] == 2:
            return render_template('index.html')
        #return render_template('.html')
    else:
        return render_template('login.html', error='Usuario y contraseña incorrectos')

@app.route('/crearusuario', methods=['GET', 'POST'])
def crearusuario():
    if request.method == 'POST':
        if 'nombre' in request.form:
            email = request.form['email']
            password = request.form['password']

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO usuario (email, password, id_rol) VALUES (%s, %s, %s)", (email, password, 2))
            mysql.connection.commit()
            cursor.close()
            return redirect(url_for('login'))
        return render_template('login.html', error='Usuario Registrado Exitosamente')

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/acercaDe')
def acercaDe():
    return render_template('acercaDe.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True, port=8000)