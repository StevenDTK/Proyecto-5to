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
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("SELECT * FROM usuario WHERE email = %s AND password = %s", (email, password))
            user = cursor.fetchone()
        finally:
            cursor.close()

        if user:
            session['logueado'] = True
            session['id'] = user['id']
            session['id_rol'] = user['id_rol']
            session['nombre'] = user.get('nombre') or user.get('email')

            if user['id_rol'] == 1:
                return redirect(url_for('admin'))
            elif user['id_rol'] == 2:
                return redirect(url_for('usuario_dashboard'))
            else:
                flash('Rol de usuario no válido', 'warning')
                return redirect(url_for('login'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/crearusuario', methods=['GET', 'POST'])
def crearusuario():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email y contraseña son requeridos', 'warning')
            return redirect(url_for('crearusuario'))

        cursor = mysql.connection.cursor()
        try:
            # verificar si el email ya existe
            cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('El correo ya está registrado', 'warning')
                return redirect(url_for('crearusuario'))

            # insertar usuario con id_rol = 2 (usuario)
            cursor.execute(
                "INSERT INTO usuario (email, password, id_rol) VALUES (%s, %s, %s)",
                (email, password, 2)
            )
            mysql.connection.commit()
            flash('Usuario creado correctamente. Puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()
            print("Error al crear usuario:", e)
            flash('Ocurrió un error al crear el usuario', 'danger')
            return redirect(url_for('crearusuario'))
        finally:
            cursor.close()

    # GET -> mostrar formulario de registro (crea crearusuario.html si no existe)
    return render_template('crearusuario.html')

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin')
def admin():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM usuario")
        num_users = cursor.fetchone().get('total', 0)

        cursor.execute("SELECT COUNT(*) AS total FROM servicios")
        num_servicios = cursor.fetchone().get('total', 0)

        cursor.execute("SELECT COUNT(*) AS total FROM servicios_agregados")
        num_solicitados = cursor.fetchone().get('total', 0)
    except Exception as e:
        print("Error calculando contadores en admin:", e)
        num_users = num_servicios = num_solicitados = 0
    finally:
        cursor.close()

    return render_template('admin.html',
                           num_users=num_users,
                           num_servicios=num_servicios,
                           num_solicitados=num_solicitados)

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
                   sa.estado,
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

@app.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    nuevo_estado = request.form.get('estado')
    if nuevo_estado not in ('Solicitado', 'En proceso', 'Completado', 'Cancelado'):
        flash('Estado no válido', 'warning')
        return redirect(url_for('listar_servicios'))

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("UPDATE servicios_agregados SET estado = %s WHERE id = %s", (nuevo_estado, id))
        mysql.connection.commit()
        flash('Estado actualizado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print("Error al actualizar estado:", e)
        flash('No se pudo actualizar el estado', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('listar_servicios'))

@app.route('/listar_productos_agregados')
def listar_productos_agregados():
    return redirect(url_for('listar_servicios_agregados'))

@app.route('/listar_productos')
def listar_productos():
    return redirect(url_for('listar_servicios'))

@app.route('/listar')
def listar():
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT id, email, id_rol FROM usuario ORDER BY id")
        usuarios = cursor.fetchall()
    except Exception as e:
        print("Error al listar usuarios:", e)
        usuarios = []
    finally:
        cursor.close()
    return render_template('listar_usuarios.html', usuarios=usuarios)


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            id_rol = request.form.get('id_rol') or 2

            if not email:
                flash('El email es obligatorio', 'warning')
                return redirect(url_for('editar_usuario', id=id))

            if password:
                cursor.execute(
                    "UPDATE usuario SET email = %s, password = %s, id_rol = %s WHERE id = %s",
                    (email, password, id_rol, id)
                )
            else:
                cursor.execute(
                    "UPDATE usuario SET email = %s, id_rol = %s WHERE id = %s",
                    (email, id_rol, id)
                )
            mysql.connection.commit()
            flash('Usuario actualizado', 'success')
            return redirect(url_for('listar'))
        else:
            cursor.execute("SELECT id, email, id_rol FROM usuario WHERE id = %s LIMIT 1", (id,))
            usuario = cursor.fetchone()
            if not usuario:
                flash('Usuario no encontrado', 'warning')
                return redirect(url_for('listar'))
            return render_template('editar_usuario.html', usuario=usuario)
    except Exception as e:
        mysql.connection.rollback()
        print("Error al editar usuario:", e)
        flash('Ocurrió un error al actualizar el usuario', 'danger')
        return redirect(url_for('listar'))
    finally:
        cursor.close()


@app.route('/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("DELETE FROM usuario WHERE id = %s", (id,))
        mysql.connection.commit()
        flash('Usuario eliminado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print("Error al eliminar usuario:", e)
        flash('No se pudo eliminar el usuario', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('listar'))

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/usuario')
def usuario_dashboard():
    # vista principal para usuario con rol 2
    if not session.get('logueado') or session.get('id_rol') != 2:
        flash('Acceso no autorizado', 'warning')
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    try:
        # servicios disponibles totales
        cursor.execute("SELECT COUNT(*) AS total FROM servicios")
        num_servicios = cursor.fetchone().get('total', 0)

        # solicitudes del usuario (por nombre de sesión)
        cliente_nombre = session.get('nombre')
        cursor.execute("SELECT COUNT(*) AS total FROM servicios_agregados WHERE cliente_nombre = %s", (cliente_nombre,))
        num_mis_solicitudes = cursor.fetchone().get('total', 0)
    except Exception as e:
        print("Error calculando contadores en usuario_dashboard:", e)
        num_servicios = num_mis_solicitudes = 0
    finally:
        cursor.close()

    return render_template('user_dashboard.html',
                           num_servicios=num_servicios,
                           num_mis_solicitudes=num_mis_solicitudes)

@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if not session.get('logueado') or session.get('id_rol') != 2:
        flash('Acceso no autorizado', 'warning')
        return redirect(url_for('login'))

    user_id = session.get('id')
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            nombre = request.form.get('nombre')
            email = request.form.get('email')
            password = request.form.get('password')

            if not email:
                flash('Email requerido', 'warning')
                return redirect(url_for('perfil'))

            if password:
                cursor.execute("UPDATE usuario SET nombre=%s, email=%s, password=%s WHERE id=%s",
                               (nombre, email, password, user_id))
            else:
                cursor.execute("UPDATE usuario SET nombre=%s, email=%s WHERE id=%s",
                               (nombre, email, user_id))
            mysql.connection.commit()
            session['nombre'] = nombre if nombre else email
            flash('Perfil actualizado', 'success')
            return redirect(url_for('perfil'))
        else:
            cursor.execute("SELECT id, nombre, email FROM usuario WHERE id = %s LIMIT 1", (user_id,))
            usuario = cursor.fetchone()
            return render_template('perfil.html', usuario=usuario)
    except Exception as e:
        mysql.connection.rollback()
        print("Error en perfil:", e)
        flash('Ocurrió un error', 'danger')
        return redirect(url_for('usuario_dashboard'))
    finally:
        cursor.close()

@app.route('/catalogo_servicios_usuario', methods=['GET', 'POST'])
def catalogo_servicios_usuario():
    if not session.get('logueado') or session.get('id_rol') != 2:
        flash('Acceso no autorizado', 'warning')
        return redirect(url_for('login'))

    servicio_id = request.args.get('id')
    cursor = mysql.connection.cursor()
    try:
        if request.method == 'POST':
            servicio_id = request.form.get('servicio_id')
            telefono = request.form.get('telefono')
            descripcion_cliente = request.form.get('descripcion_cliente')
            cliente_nombre = session.get('nombre')

            cursor.execute(
                """INSERT INTO servicios_agregados (servicio_id, cliente_nombre, telefono, descripcion_cliente)
                   VALUES (%s, %s, %s, %s)""",
                (servicio_id, cliente_nombre, telefono, descripcion_cliente)
            )
            mysql.connection.commit()
            flash('Solicitud enviada correctamente', 'success')
            return redirect(url_for('mis_servicios'))
        else:
            if servicio_id:
                cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios WHERE id = %s", (servicio_id,))
                servicio = cursor.fetchone()
                return render_template('catalogo_servicios_usuario.html', servicio=servicio)
            else:
                cursor.execute("SELECT id, nombre, descripcion, precio FROM servicios")
                servicios = cursor.fetchall()
                return render_template('catalogo_servicios_usuario.html', servicios=servicios)
    except Exception as e:
        mysql.connection.rollback()
        print("Error catálogo usuario:", e)
        flash('Ocurrió un error', 'danger')
        return redirect(url_for('usuario_dashboard'))
    finally:
        cursor.close()

@app.route('/mis_servicios')
def mis_servicios():
    if not session.get('logueado') or session.get('id_rol') != 2:
        flash('Acceso no autorizado', 'warning')
        return redirect(url_for('login'))

    cliente_nombre = session.get('nombre')
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            SELECT sa.id, sa.cliente_nombre, sa.telefono, sa.descripcion_cliente, sa.creado_at, sa.estado,
                   s.id AS servicio_id, s.nombre AS servicio_nombre, s.descripcion AS servicio_descripcion, s.precio AS servicio_precio
            FROM servicios_agregados sa
            JOIN servicios s ON sa.servicio_id = s.id
            WHERE sa.cliente_nombre = %s
            ORDER BY sa.creado_at DESC
        """, (cliente_nombre,))
        servicios = cursor.fetchall()
    except Exception as e:
        print("Error al consultar mis servicios:", e)
        servicios = []
    finally:
        cursor.close()
    return render_template('mis_servicios.html', servicios=servicios)

@app.route('/cancelar_servicio/<int:id>', methods=['POST'])
def cancelar_servicio(id):
    if not session.get('logueado') or session.get('id_rol') != 2:
        flash('Acceso no autorizado', 'warning')
        return redirect(url_for('login'))

    cliente_nombre = session.get('nombre')
    cursor = mysql.connection.cursor()
    try:
        # verificar que el registro pertenezca al usuario
        cursor.execute("SELECT cliente_nombre FROM servicios_agregados WHERE id = %s LIMIT 1", (id,))
        row = cursor.fetchone()
        if not row or row.get('cliente_nombre') != cliente_nombre:
            flash('Acción no permitida', 'warning')
            return redirect(url_for('mis_servicios'))

        cursor.execute("UPDATE servicios_agregados SET estado = %s WHERE id = %s", ('Cancelado', id))
        mysql.connection.commit()
        flash('Servicio cancelado', 'success')
    except Exception as e:
        mysql.connection.rollback()
        print("Error al cancelar servicio:", e)
        flash('No se pudo cancelar el servicio', 'danger')
    finally:
        cursor.close()
    return redirect(url_for('mis_servicios'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)