from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

app=Flask(__name__)
app.secret_key = 'appsecretkey'
mysql=MySQL()

app.config['MYSQL_HOST'] = 'bac3h58ceealmbvwi4j5-mysql.services.clever-cloud.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'utamd4d06im5dn5p'
app.config['MYSQL_PASSWORD'] = 'mts6lfWFx67un22FNwSq'
app.config['MYSQL_DB'] = 'bac3h58ceealmbvwi4j5'
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
                return redirect(url_for('admin'))
            elif user['id_rol'] == 2:
                return redirect(url_for('inicio'))
            else:
                return render_template('login.html', error='Rol de usuario no válido')
        else:
            return render_template('login.html', error='Usuario y contraseña incorrectos')
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

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/acercaDe')
def acercaDe():
    return render_template('acercaDe.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/listar_servicios_agregados', methods=['GET', 'POST'])
def listar_servicios_agregados():
    """
    Si GET sin id -> listar servicios (catalogo) para seleccionar.
    Si GET con id -> mostrar formulario para agregar datos del cliente para ese servicio.
    Si POST -> insertar registro en 'servicios_agregados' con servicio_id y datos del cliente.
    """
    if request.method == 'POST':
        cliente_nombre = request.form.get('cliente_nombre')
        telefono = request.form.get('telefono')
        descripcion_cliente = request.form.get('descripcion_cliente')
        servicio_id = request.form.get('servicio_id')

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO servicios_agregados
                (servicio_id, cliente_nombre, telefono, descripcion_cliente)
                VALUES (%s, %s, %s, %s)
                """,
                (servicio_id, cliente_nombre, telefono, descripcion_cliente)
            )
            mysql.connection.commit()
            flash('Servicio asignado al cliente correctamente', 'success')
        except Exception as e:
            mysql.connection.rollback()
            print("Error al insertar servicio agregado:", e)
            flash('Ocurrió un error al guardar. Revisa la consola.', 'danger')
        finally:
            cursor.close()
        return redirect(url_for('listar_servicios_agregados'))

    servicio_id = request.args.get('id')
    cursor = mysql.connection.cursor()
    try:
        if servicio_id:
            cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios WHERE id = %s", (servicio_id,))
            servicio = cursor.fetchone()
            return render_template('listar_servicios_agregados.html', servicio=servicio)
        else:
            cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios")
            servicios = cursor.fetchall()
            return render_template('listar_servicios_agregados.html', servicios=servicios)  # <-- asegúrate de devolver 'servicios' en el else
    except Exception as e:
        print("Error al consultar servicios para agregados:", e)
        return render_template('listar_servicios_agregados.html', servicios=[])
    finally:
        cursor.close()

@app.route('/listar_servicios')
def listar_servicios():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            SELECT sa.id,
                   sa.cliente_nombre,
                   sa.telefono,
                   sa.descripcion_cliente,
                   sa.creado_at,
                   s.id AS servicio_id,
                   s.nombre AS servicio_nombre,
                   s.descripcion AS servicio_descripcion,
                   s.precio AS servicio_precio
            FROM servicios_agregados sa
            JOIN servicios s ON sa.servicio_id = s.id
            ORDER BY sa.creado_at DESC
        """)
        servicios = cursor.fetchall()
    except Exception as e:
        print("Error al consultar servicios agregados:", e)
        servicios = []
    finally:
        cursor.close()

    return render_template('listar_servicios.html', servicios=servicios)

@app.route('/listar_productos_agregados')
def listar_productos_agregados():
    return redirect(url_for('listar_servicios_agregados'))

@app.route('/listar_productos')
def listar_productos():
    return redirect(url_for('listar_servicios'))

@app.route('/listar')
def listar():
    return "Página de perfil de usuario"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/servicios_agregados')
def servicios_agregados():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            SELECT sa.id, sa.cliente_nombre, sa.telefono, sa.descripcion_cliente, sa.creado_at,
                   s.id AS servicio_id, s.nombre AS servicio_nombre, s.descripcion AS servicio_descripcion, s.precio AS servicio_precio
            FROM servicios_agregados sa
            JOIN servicios s ON sa.servicio_id = s.id
            ORDER BY sa.creado_at DESC
        """)
        rows = cursor.fetchall()
    except Exception as e:
        print("Error al listar servicios agregados:", e)
        rows = []
    finally:
        cursor.close()
    return render_template('servicios_agregados.html', rows=rows)

@app.route('/editar_servicio_agregado/<int:id>', methods=['GET', 'POST'])
def editar_servicio_agregado(id):
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            cliente_nombre = request.form.get('cliente_nombre')
            telefono = request.form.get('telefono')
            descripcion_cliente = request.form.get('descripcion_cliente')
            cursor.execute(
                """
                UPDATE servicios_agregados
                SET cliente_nombre = %s, telefono = %s, descripcion_cliente = %s
                WHERE id = %s
                """,
                (cliente_nombre, telefono, descripcion_cliente, id)
            )
            mysql.connection.commit()
            flash('Datos del cliente actualizados', 'success')
            return redirect(url_for('listar_servicios'))
        else:
            cursor.execute("""
                SELECT sa.id, sa.cliente_nombre, sa.telefono, sa.descripcion_cliente, sa.creado_at,
                       s.id AS servicio_id, s.nombre AS servicio_nombre, s.descripcion AS servicio_descripcion, s.precio AS servicio_precio
                FROM servicios_agregados sa
                JOIN servicios s ON sa.servicio_id = s.id
                WHERE sa.id = %s
                LIMIT 1
            """, (id,))
            registro = cursor.fetchone()
            if not registro:
                flash('Registro no encontrado', 'warning')
                return redirect(url_for('listar_servicios'))
            return render_template('editar_servicio_agregado.html', registro=registro)
    except Exception as e:
        mysql.connection.rollback()
        print("Error editar servicio agregado:", e)
        flash('Ocurrió un error', 'danger')
        return redirect(url_for('listar_servicios'))
    finally:
        cursor.close()

@app.route('/eliminar_servicio_agregado/<int:id>', methods=['POST'])
def eliminar_servicio_agregado(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM servicios_agregados WHERE id = %s", (id,))
        mysql.connection.commit()
        flash('Servicio agregado eliminado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print("Error al eliminar servicio agregado:", e)
        flash('Ocurrió un error al eliminar', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('listar_servicios'))

# --- nuevas rutas para gestionar la tabla `servicios` ---
@app.route('/nuevo_servicio', methods=['GET', 'POST'])
def nuevo_servicio():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        precio = request.form.get('precio') or 0
        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO servicios (nombre, descripcion, precio) VALUES (%s, %s, %s)",
                (nombre, descripcion, precio)
            )
            mysql.connection.commit()
            flash('Servicio creado correctamente', 'success')
            return redirect(url_for('listar_servicios_agregados'))
        except Exception as e:
            mysql.connection.rollback()
            print("Error al crear servicio:", e)
            flash('No se pudo crear el servicio', 'danger')
        finally:
            cursor.close()
    return render_template('nuevo_servicio.html')

@app.route('/editar_servicio/<int:id>', methods=['GET', 'POST'])
def editar_servicio(id):
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio = request.form.get('precio') or 0
            cursor.execute(
                "UPDATE servicios SET nombre = %s, descripcion = %s, precio = %s WHERE id = %s",
                (nombre, descripcion, precio, id)
            )
            mysql.connection.commit()
            flash('Servicio actualizado', 'success')
            return redirect(url_for('listar_servicios_agregados'))
        else:
            cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios WHERE id = %s LIMIT 1", (id,))
            servicio = cursor.fetchone()
            if not servicio:
                flash('Servicio no encontrado', 'warning')
                return redirect(url_for('listar_servicios_agregados'))
            return render_template('editar_servicio.html', servicio=servicio)
    except Exception as e:
        mysql.connection.rollback()
        print("Error al editar servicio:", e)
        flash('Ocurrió un error', 'danger')
        return redirect(url_for('listar_servicios_agregados'))
    finally:
        cursor.close()

@app.route('/eliminar_servicio/<int:id>', methods=['POST'])
def eliminar_servicio(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM servicios WHERE id = %s", (id,))
        mysql.connection.commit()
        flash('Servicio eliminado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print("Error al eliminar servicio (posible FK):", e)
        flash('No se pudo eliminar el servicio. Verifica dependencias.', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('listar_servicios_agregados'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)