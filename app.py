import string
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configuración base de datos
if os.environ.get("FLASK_ENV") == "production":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://catalogo_1kp6_user:rMZ0nuyPp7W5OVXu1b7tMq3BqIafLBjJ@dpg-d1jg87emcj7s73dcr2o0-a.oregon-postgres.render.com/catalogo_1kp6'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos

class Libro(db.Model):
    __tablename__ = 'libros'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150))
    genero = db.Column(db.String(100))
    editorial = db.Column(db.String(150))
    anio = db.Column(db.Integer)
    ubicacion = db.Column(db.String(100))
    estado = db.Column(db.String(50), default='Disponible')

    prestamos = db.relationship('Prestamo', backref='libro', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Libro {self.titulo}>"


class Prestamo(db.Model):
    __tablename__ = 'prestamos'

    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    nombre_lector = db.Column(db.String(150), nullable=False)
    fecha_prestamo = db.Column(db.Date, nullable=False)
    fecha_devolucion = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<Prestamo libro_id={self.libro_id} lector={self.nombre_lector}>"

# ---- CATÁLOGO SIMULADO ----

catalogo_simulado = [
    {
        'id': 1,
        'titulo': 'Harry Potter',
        'autor': 'J.K. Rowling',
        'genero': 'Fantasía',
        'editorial': 'Salamandra',
        'anio': 1997,
        'ubicacion': 'Estante A3',
        'estado': 'Disponible'
    },
    {
        'id': 2,
        'titulo': 'Cien Años de Soledad',
        'autor': 'Gabriel García Márquez',
        'genero': 'Realismo Mágico',
        'editorial': 'Sudamericana',
        'anio': 1967,
        'ubicacion': 'Estante B1',
        'estado': 'Prestado'
    },
    {
        'id': 3,
        'titulo': 'Don Quijote',
        'autor': 'Miguel de Cervantes',
        'genero': 'Novela',
        'editorial': 'Francisco de Robles',
        'anio': 1605,
        'ubicacion': 'Estante C2',
        'estado': 'Disponible'
    }
]

# Crear tablas si no existen
with app.app_context():
    db.create_all()

# ---- RUTAS ----

@app.route('/')
def inicio():
    return render_template('inicio.html')


@app.route('/buscar')
def buscar():
    query = request.args.get('query', '')
    letra = request.args.get('letra', '')

    letras = list(string.ascii_uppercase)

    try:
        catalogo = Libro.query.all()
        catalogo = [{
            'id': libro.id,
            'titulo': libro.titulo,
            'autor': libro.autor,
            'genero': libro.genero,
            'editorial': libro.editorial,
            'anio': libro.anio,
            'ubicacion': libro.ubicacion,
            'estado': libro.estado
        } for libro in catalogo]
    except Exception as e:
        print("Error al consultar DB:", e)
        catalogo = catalogo_simulado.copy()

    if query:
        catalogo = [
            libro for libro in catalogo
            if query.lower() in libro['titulo'].lower()
        ]

    if letra:
        catalogo = [
            libro for libro in catalogo
            if libro['titulo'].upper().startswith(letra)
        ]

    catalogo.sort(key=lambda x: x['titulo'])

    return render_template(
        'buscar.html',
        letras=letras,
        catalogo=catalogo,
        query=query,
        letra=letra
    )


@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        autor = request.form.get('autor')
        genero = request.form.get('genero')
        editorial = request.form.get('editorial')
        anio = request.form.get('anio')
        ubicacion = request.form.get('ubicacion')

        # Validar campos llenos
        if not all([titulo, autor, genero, editorial, anio, ubicacion]):
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for('registrar'))

        # ✅ MODIFICADO → Validar año es número y de 4 dígitos
        try:
            anio_int = int(anio)
            if anio_int < 1000 or anio_int > 9999:
                flash("El año debe ser un número de 4 dígitos.", "danger")
                return redirect(url_for('registrar'))
        except ValueError:
            flash("El año debe ser numérico.", "danger")
            return redirect(url_for('registrar'))

        # ✅ MODIFICADO → Validar duplicado (mismo título y autor)
        existing = Libro.query.filter_by(titulo=titulo, autor=autor).first()
        if existing:
            flash("Ese libro ya está registrado.", "warning")
            return redirect(url_for('registrar'))

        try:
            libro_nuevo = Libro(
                titulo=titulo,
                autor=autor,
                genero=genero,
                editorial=editorial,
                anio=anio_int,
                ubicacion=ubicacion,
                estado='Disponible'
            )
            db.session.add(libro_nuevo)
            db.session.commit()
            flash("Libro registrado correctamente.", "success")
            return redirect(url_for('buscar'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al registrar libro: {e}", "danger")
            return redirect(url_for('registrar'))

    return render_template('registrar.html')


@app.route('/baja', methods=['POST'])
def baja():
    id_baja = request.form.get('id_baja')

    if not id_baja:
        flash("ID para baja no proporcionado.", "danger")
        return redirect(url_for('buscar'))

    try:
        libro = Libro.query.get(int(id_baja))
        if libro:
            db.session.delete(libro)
            db.session.commit()
            flash(f"Libro con ID {id_baja} eliminado correctamente.", "success")
        else:
            flash(f"No se encontró libro con ID {id_baja}.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar libro: {e}", "danger")

    return redirect(url_for('buscar'))


@app.route('/prestamos', methods=['GET', 'POST'])
def prestamos():
    if request.method == 'POST':
        libro_id = request.form.get("libro_id")
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

            prestamo_nuevo = Prestamo(
                libro_id=libro.id,
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

    try:
        prestamos = Prestamo.query.join(Libro).add_columns(
            Prestamo.id, Libro.titulo, Prestamo.nombre_lector,
            Prestamo.fecha_prestamo, Prestamo.fecha_devolucion
        ).all()

        prestamos_list = []
        for p in prestamos:
            prestamos_list.append({
                'id': p.id,
                'titulo': p.titulo,
                'nombre_lector': p.nombre_lector,
                'fecha_prestamo': p.fecha_prestamo.strftime('%Y-%m-%d'),
                'fecha_devolucion': p.fecha_devolucion.strftime('%Y-%m-%d')
            })
    except Exception as e:
        print("Error al cargar préstamos:", e)
        prestamos_list = [
            {
                'id': 1,
                'titulo': 'Harry Potter',
                'nombre_lector': 'Juan Pérez',
                'fecha_prestamo': '2025-07-04',
                'fecha_devolucion': '2025-07-10'
            },
            {
                'id': 2,
                'titulo': 'Don Quijote',
                'nombre_lector': 'Ana Gómez',
                'fecha_prestamo': '2025-07-03',
                'fecha_devolucion': '2025-07-15'
            }
        ]

    return render_template('prestamos.html', prestamos=prestamos_list)


@app.route('/devolver', methods=['POST'])
def devolver_libro():
    libro_id = request.form.get("libro_id_devolver")

    if not libro_id:
        flash("ID para devolución no proporcionado.", "danger")
        return redirect(url_for('prestamos'))

    try:
        libro = Libro.query.get(int(libro_id))
        if not libro:
            flash("Libro no encontrado.", "danger")
            return redirect(url_for('prestamos'))

        libro.estado = 'Disponible'

        prestamo = Prestamo.query.filter_by(libro_id=libro.id).first()
        if prestamo:
            db.session.delete(prestamo)

        db.session.commit()
        flash(f"¡Libro con ID {libro_id} devuelto correctamente!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar devolución: {e}", "danger")

    return redirect(url_for('prestamos'))


if __name__ == '__main__':
    app.run(debug=True)