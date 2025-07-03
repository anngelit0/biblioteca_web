import string
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/buscar')
def buscar():
    query = request.args.get('query', '')
    letra = request.args.get('letra', '')

    letras = list(string.ascii_uppercase)

    catalogo = [
        {'titulo': 'Harry Potter', 'autor': 'J.K. Rowling'},
        {'titulo': 'Cien Años de Soledad', 'autor': 'Gabriel García Márquez'},
        {'titulo': 'Don Quijote', 'autor': 'Miguel de Cervantes'},
        {'titulo': 'Alicia en el País de las Maravillas', 'autor': 'Lewis Carroll'}
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

@app.route('/prestamos')
def prestamos():
    return render_template('prestamos.html')

if __name__ == '__main__':
    app.run(debug=True)
