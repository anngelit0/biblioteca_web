import string
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Para mensajes flash

# Conexión fija a PostgreSQL en Render
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://catalogo_1kp6_user:rMZ0nuyPp7W5OVXu1b7tMq3BqIafLBjJ@dpg-d1jg87emcj7s73dcr2o0-a.oregon-postgres.render.com/catalogo_1kp6'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------
# MODELOS
# -----------------------

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
    prestamos = db.relationship('Prestamo', backref='libro', cascade="all, delete-orphan")

class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)  # Campo título en préstamo
    nombre_lector = db.Column(db.String(150), nullable=False)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=False)

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# -----------------------
# RUTAS
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

    # Filtrado
    if query:
        catalogo = [libro for libro in catalogo if query.lower() in libro.titulo.lower()]
    if letra:
        catalogo = [libro for libro in catalogo if libro.titulo.upper().startswith(letra)]

    # Orden alfabético
    catalogo.sort(key=lambda x: x.titulo)

    return render_template('buscar.html', letras=letras, catalogo=catalogo, query=query, letra=letra)

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        datos = {k: request.form.get(k) for k in ['titulo', 'autor', 'genero', 'editorial', 'anio', 'ubicacion']}
        if not all(datos.values()):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for('registrar'))

        try:
            libro = Libro(
                titulo=datos['titulo'],
                autor=datos['autor'],
                genero=datos['genero'],
                editorial=datos['editorial'],
                anio=int(datos['anio']),
                ubicacion=datos['ubicacion'],
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