import string
import os
from flask import Flask, render_template, request

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

if os.environ.get("FLASK_ENV") == "production":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://catalogo_1kp6_user:rMZ0nuyPp7W5OVXu1b7tMq3BqIafLBj@dpg-d1jg87emcj7s73dcr2o0-a/catalogo_1kp6'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Libro(db.Model):
    __tablename__ = 'libros'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    autor = db.Column(db.String(150), nullable=True)
    genero = db.Column(db.String(100), nullable=True)
    editorial = db.Column(db.String(150), nullable=True)
    anio = db.Column(db.Integer, nullable=True)
    ubicacion = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(50), nullable=True)
    
    def __repr__(self):
        return f"<Libro {self.titulo}>"

# Para crear las tablas en la base de datos (solo la primera vez)
with app.app_context():
    db.create_all()


@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/buscar')
def buscar():
    query = request.args.get('query', '')
    letra = request.args.get('letra', '')

    letras = list(string.ascii_uppercase)

    catalogo = [
        {
            'titulo': 'Harry Potter',
            'autor': 'J.K. Rowling',
            'genero': 'Fantasía',
            'editorial': 'Salamandra',
            'anio': 1997,
            'ubicacion': 'Estante A3',
            'estado': 'Disponible'
        },
        {
            'titulo': 'Cien Años de Soledad',
            'autor': 'Gabriel García Márquez',
            'genero': 'Realismo Mágico',
            'editorial': 'Sudamericana',
            'anio': 1967,
            'ubicacion': 'Estante B1',
            'estado': 'Prestado'
        },
        {
            'titulo': 'Don Quijote',
            'autor': 'Miguel de Cervantes',
            'genero': 'Novela',
            'editorial': 'Francisco de Robles',
            'anio': 1605,
            'ubicacion': 'Estante C2',
            'estado': 'Disponible'
        }
    ]

    # Filtrado por búsqueda
    if query:
        catalogo = [libro for libro in catalogo if query.lower() in libro['titulo'].lower()]

    # Filtrado por letra
    if letra:
        catalogo = [libro for libro in catalogo if libro['titulo'].upper().startswith(letra)]

    # Orden alfabético
    catalogo.sort(key=lambda x: x['titulo'])

    return render_template(
        'buscar.html',
        letras=letras,
        catalogo=catalogo,
        query=query,
        letra=letra
    )

@app.route('/registrar')
def registrar():
    return render_template('registrar.html')

@app.route('/prestamo', methods=['POST'])
def registrar_prestamo():
    # Lógica aquí…
    return render_template('prestamos.html', mensaje_tomar="¡Disfruta tu lectura!")

@app.route('/devolver', methods=['POST'])
def devolver_libro():
    # Lógica aquí…
    return render_template('prestamos.html', mensaje_devolver="¡Libro devuelto correctamente!")


if __name__ == '__main__':
    app.run(debug=True)
