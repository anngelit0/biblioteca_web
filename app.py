import string
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necesario para flash()

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


# ---- RUTAS ----

@app.route('/')
def inicio():
    return render_template('inicio.html')


@app.route('/buscar')
def buscar():
    query = request.args.get('query', '')
    letra = request.args.get('letra', '')

    letras = list(string.ascii_uppercase)

    catalogo = catalogo_simulado.copy()

    # Filtrado por búsqueda
    if query:
        catalogo = [
            libro for libro in catalogo
            if query.lower() in libro['titulo'].lower()
        ]

    # Filtrado por letra
    if letra:
        catalogo = [
            libro for libro in catalogo
            if libro['titulo'].upper().startswith(letra)
        ]

    # Ordenar alfabéticamente
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
        # Obtenemos los datos del formulario
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

        # SIMULADO: solo mostramos mensaje (no se guarda nada todavía)
        flash("Libro registrado correctamente (SIMULADO).", "success")
        return redirect(url_for('buscar'))

    return render_template('registrar.html')


@app.route('/baja', methods=['POST'])
def baja():
    id_baja = request.form.get('id_baja')

    # SIMULADO: solo mostramos mensaje
    flash(f"Libro con ID {id_baja} eliminado correctamente (SIMULADO).", "success")

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

        # SIMULADO: solo mostramos mensaje
        flash("Préstamo registrado correctamente (SIMULADO).", "success")
        return redirect(url_for('prestamos'))

    # Simulación de préstamos activos
    prestamos_simulados = [
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

    return render_template(
        'prestamos.html',
        prestamos=prestamos_simulados
    )


@app.route('/devolver', methods=['POST'])
def devolver_libro():
    libro_id = request.form.get("libro_id_devolver")

    # SIMULADO: solo mostramos mensaje
    flash(f"¡Libro con ID {libro_id} devuelto correctamente (SIMULADO)!", "success")

    return redirect(url_for('prestamos'))


if __name__ == '__main__':
    app.run(debug=True)