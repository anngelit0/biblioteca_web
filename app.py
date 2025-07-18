# ... [Líneas iniciales sin cambios] ...
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, session, flash
import string
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Conexión a PostgreSQL en Render
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://catalogo_1kp6_user:rMZ0nuyPp7W5OVXu1b7tMq3BqIafLBjJ@dpg-d1jg87emcj7s73dcr2o0-a.oregon-postgres.render.com/catalogo_1kp6'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------
# MODELOS
# -----------------------

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(200), nullable=False)
    pregunta_seguridad = db.Column(db.String(200), nullable=False)
    respuesta_seguridad_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, contrasena):
        self.contrasena_hash = generate_password_hash(contrasena)

    def check_password(self, contrasena):
        return check_password_hash(self.contrasena_hash, contrasena)

    def set_respuesta_seguridad(self, respuesta):
        self.respuesta_seguridad_hash = generate_password_hash(respuesta.lower())

    def check_respuesta_seguridad(self, respuesta):
        return check_password_hash(self.respuesta_seguridad_hash, respuesta.lower())

class Libro(db.Model):
    __tablename__ = 'libros'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=False)
    genero = db.Column(db.String(100), nullable=False)
    editorial = db.Column(db.String(150), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    ubicacion = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='Disponible')
    idioma = db.Column(db.String(100), nullable=True)   # Nuevo campo
    casa = db.Column(db.String(100), nullable=True)     # Nuevo campo
    prestamos = db.relationship('Prestamo', backref='libro', cascade="all, delete-orphan")

class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    nombre_lector = db.Column(db.String(150), nullable=False)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()

# -----------------------
# RUTAS

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']
        pregunta_seguridad = request.form['pregunta_seguridad']
        respuesta_seguridad = request.form['respuesta_seguridad']

        if Usuario.query.filter_by(nombre_usuario=nombre_usuario).first():
            flash("El nombre de usuario ya existe", "danger")
            return redirect(url_for('registro'))

        nuevo_usuario = Usuario(
            nombre_usuario=nombre_usuario,
            pregunta_seguridad=pregunta_seguridad
        )
        nuevo_usuario.set_password(contrasena)
        nuevo_usuario.set_respuesta_seguridad(respuesta_seguridad)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Registro exitoso. Por favor inicia sesión.", "success")
        return redirect(url_for('login'))
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre_usuario = request.form['nombre_usuario']
        contrasena = request.form['contrasena']

        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario and usuario.check_password(contrasena):
            session.clear()
            session['user_id'] = usuario.id
            flash("Sesión iniciada", "success")
            return redirect(url_for('inicio'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
    return render_template('login.html')

@app.route('/invitado')
def invitado():
    session.clear()
    session['guest'] = True
    flash("Entraste como invitado", "info")
    return redirect(url_for('inicio'))
# -----------------------

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/buscar')
def buscar():
    query = request.args.get('query', '')
    letra = request.args.get('letra', '')
    letras = list(string.ascii_uppercase)

    catalogo = Libro.query.all()

    if query:
        catalogo = [libro for libro in catalogo if query.lower() in libro.titulo.lower()]
    if letra:
        catalogo = [libro for libro in catalogo if libro.titulo.upper().startswith(letra)]

    catalogo.sort(key=lambda x: x.titulo)

    return render_template('buscar.html', letras=letras, catalogo=catalogo, query=query, letra=letra)

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        datos = {k: request.form.get(k) for k in ['titulo', 'autor', 'genero', 'editorial', 'anio', 'ubicacion', 'idioma', 'casa']}
        if not all([datos[k] for k in ['titulo', 'autor', 'genero', 'editorial', 'anio', 'ubicacion']]):
            flash("Todos los campos obligatorios deben completarse.", "danger")
            return redirect(url_for('registrar'))

        try:
            libro = Libro(
                titulo=datos['titulo'],
                autor=datos['autor'],
                genero=datos['genero'],
                editorial=datos['editorial'],
                anio=int(datos['anio']),
                ubicacion=datos['ubicacion'],
                idioma=datos.get('idioma'),
                casa=datos.get('casa'),
                estado='Disponible'
            )
            db.session.add(libro)
            db.session.commit()
            flash("Libro registrado correctamente.", "success")
            return redirect(url_for('buscar'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar libro: {e}", "danger")
            return redirect(url_for('registrar'))

    return render_template('registrar.html')

@app.route('/prestamos', methods=['GET', 'POST'])
def prestamos():
    # Obtener parámetros GET (cuando se abre el formulario desde buscar)
    libro_id = request.args.get("libro_id")
    titulo_libro = request.args.get("titulo")

    if request.method == 'POST':
        libro_id = request.form.get("libro_id")
        titulo = request.form.get("titulo")
        nombre = request.form.get("nombre")
        fecha_prestamo = request.form.get("fecha_prestamo")
        fecha_devolucion = request.form.get("fecha_devolucion")

        if not all([libro_id, nombre, fecha_prestamo, fecha_devolucion]):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for('prestamos'))

        try:
            libro = Libro.query.get(int(libro_id))
            if not libro:
                flash("Libro no encontrado.", "danger")
                return redirect(url_for('prestamos'))

            if libro.estado == 'Prestado':
                flash("El libro ya está prestado.", "warning")
                return redirect(url_for('prestamos'))

            # Si no se pasó título por el form, tomarlo del libro
            if not titulo:
                titulo = libro.titulo

            prestamo_nuevo = Prestamo(
                libro_id=libro.id,
                titulo=titulo,
                nombre_lector=nombre,
                fecha_prestamo=datetime.strptime(fecha_prestamo, '%Y-%m-%d').date(),
                fecha_devolucion=datetime.strptime(fecha_devolucion, '%Y-%m-%d').date()
            )
            libro.estado = 'Prestado'

            db.session.add(prestamo_nuevo)
            db.session.commit()
            flash("Préstamo registrado correctamente.", "success")
            return redirect(url_for('prestamos'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar préstamo: {e}", "danger")
            return redirect(url_for('prestamos'))

    # Consultar préstamos existentes para mostrar
    try:
        prestamos = Prestamo.query.all()
        prestamos_list = []
        for p in prestamos:
            prestamos_list.append({
                'libro_id': p.libro_id,  # Corregido para que sea 'libro_id' aquí también
                'titulo': p.titulo,
                'nombre_lector': p.nombre_lector,
                'fecha_prestamo': p.fecha_prestamo.strftime('%Y-%m-%d'),
                'fecha_devolucion': p.fecha_devolucion.strftime('%Y-%m-%d')
            })
    except Exception as e:
        print("Error al cargar préstamos:", e)
        prestamos_list = []

    # Enviar variables a la plantilla
    return render_template(
        'prestamos.html',
        prestamos=prestamos_list,
        libro_id=libro_id,
        titulo=titulo_libro if libro_id else None  # Esta es la corrección principal
    )

@app.route('/devolver', methods=['POST'])
def devolver():
    libro_id = request.form.get('libro_id_devolver')

    if not libro_id:
        flash("ID para devolución no proporcionado.", "danger")
        return redirect(url_for('prestamos'))

    libro = Libro.query.get(int(libro_id))
    if not libro:
        flash("Libro no encontrado.", "danger")
        return redirect(url_for('prestamos'))

    try:
        libro.estado = 'Disponible'
        prestamo = Prestamo.query.filter_by(libro_id=libro.id).first()
        if prestamo:
            db.session.delete(prestamo)
        db.session.commit()
        flash("Libro devuelto correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al devolver libro: {e}", "danger")

    return redirect(url_for('prestamos'))

@app.route('/baja', methods=['POST'])
def baja():
    id_baja = request.form.get('id_baja')

    if not id_baja:
        flash("ID para baja no proporcionado.", "danger")
        return redirect(url_for('buscar'))

    libro = Libro.query.get(int(id_baja))
    if not libro:
        flash("Libro no encontrado.", "warning")
        return redirect(url_for('buscar'))

    try:
        db.session.delete(libro)
        db.session.commit()
        flash(f"Libro con ID {id_baja} eliminado.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar libro: {e}", "danger")

    return redirect(url_for('buscar'))

if __name__ == '__main__':
    app.run(debug=True)