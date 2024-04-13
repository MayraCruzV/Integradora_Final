from flask import Flask, request, jsonify
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash #validar contraseñas
from flask_mail import Mail


from .models.ModeloLibro import ModeloLibro
from .models.ModeloUsuario import ModeloUsuario
from .models.ModeloCompra import ModeloCompra
from .models.entities.Usuario import Usuario, newUsuario
from .models.entities.Compra import Compra
from .models.entities.Libro import Libro

from .consts import *
from .emails import confirmacion_compra, confirmacion_registro
app = Flask(__name__)

csrf = CSRFProtect()
db = MySQL(app)
login_manager_app = LoginManager(app)
mail = Mail()


@login_manager_app.user_loader
def load_user(id):
    return ModeloUsuario.Obtener_por_id(db, id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario(None, request.form['usuario'],
                          request.form['password'], None)
        usuario_logeado = ModeloUsuario.login(db, usuario)
        if usuario_logeado != None:
            login_user(usuario_logeado)
            print("DENTRO")
            flash(MENSAJE_BIENVENIDA, 'success')
            return redirect(url_for('index'))
        else:
            flash(LOGIN_CREDENCIALESINVALIDAES, 'warning')  # usando variable
            print("VOLVER A INGRESAR CRENDENCIALES")
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html')


@app.route('/')
@login_required
def index():
    if current_user.is_authenticated:
        if current_user.tipousuario.id == 1:
            try:
                libros_vendidos= ModeloLibro.listar_libros_vendidos(db)
                data = {
                    'titulo':'Libros Vendidos',
                    'libros_vendidos':libros_vendidos
                }
                return render_template('index.html', data=data)
            except Exception as ex:
                print("error aqui")
                print(ex)
                return render_template('errores/error.html',mensaje=format(ex))
        else:
            try:
                libros=ModeloLibro.listar_libros(db)
                data={
                    'titulo':'Libros Disponibles',
                    'libros':libros
                }
                return render_template('index.html',data=data)
            except Exception as ex:
                 render_template('errores/error.html',mensaje=format(ex))
            
    else:
        return redirect(url_for('login'))
    
@app.route('/main')
def main():
    try:
        libros = ModeloLibro.listar_libros(db)
        data = {
            'titulo': 'Libros Disponibles',
            'libros': libros
        }
        return render_template('main.html', data=data)
    except Exception as ex:
        print(ex)
        return render_template('errores/error.html', mensaje=format(ex))


@app.route('/libros')
@login_required
def listar_libros():
    try:    
        compras = ModeloCompra.listar_compras_usuario(db, current_user)
        data = {
            'titulo':'Mis compras',
            'compras': compras
        }
        return render_template('listado_libros.html', data=data)
    except Exception as ex:
        print("erroraqui")
        return render_template('errores/error.html',mensaje=format(ex))


@app.route('/register')
def register():
    return render_template('auth/register.html')


@app.route('/registrar_usuario', methods=['POST'])
def registrar_usuario():
    data = {}
    try:
        # Obtener datos del formulario
        datos_formulario = request.json
        usuario = datos_formulario.get('usuario')
        password = datos_formulario.get('password')
        direccion = datos_formulario.get('direccion')
        telefono = datos_formulario.get('telefono')
        email = datos_formulario.get('email')
        password_encriptada=generate_password_hash(password)
        print(usuario, password, direccion, telefono, email)

        # Crear un nuevo objeto de usuario
        nuevo_usuario = newUsuario(
            None, usuario, password_encriptada, 2, direccion,telefono, email)

        # Instanciar un objeto de ModeloUsuario
        modelo_usuario = ModeloUsuario()

        # Registrar el nuevo usuario en la base de datos
        data['exito'] = modelo_usuario.registrar_cliente(
            db, usuario=nuevo_usuario)
        if data['exito']:
            data['mensaje'] = 'Usuario registrado correctamente'
            confirmacion_registro(app, mail, nuevo_usuario) 
        else:
            data['mensaje'] = 'Error al registrar el usuario'
    except Exception as ex:
        data['exito'] = False
        data['mensaje'] = str(ex)
    return jsonify(data)


@app.route('/comprarLibro', methods=['POST'])
@login_required
def comprar_libro():
    data_request = request.get_json()
    data = {}
    try:
        libro = ModeloLibro.leer_libro(db, data_request['isbn'])
        # libro=Libro(data_request['isbn'], None, None,None, None)
        compra = Compra(None, libro, current_user)
        data['exito'] = ModeloCompra.registrar_compra(db, compra)
        # confirmacion_compra(mail, current_user, libro) envio sincrono
        confirmacion_compra(app, mail, current_user, libro)  # encio async
    except Exception as ex:
        data['mensaje'] = format(ex)
        data['exito'] = False
    return jsonify(data)


@app.route('/logout')
def logout():
    logout_user()
    flash(LOGOUT, 'success')  # usando variable
    return redirect(url_for('login'))


def pagina_no_encontrada(errores):
    print(errores)
    return render_template('errores/404.html'), 404


def pagina_no_autorizada(error):
    print(error)
    return redirect(url_for('login'))



def inicializar_app(config):
    app.config.from_object(config)
    csrf.init_app(app)
    mail.init_app(app)
    app.register_error_handler(404, pagina_no_encontrada)
    app.register_error_handler(401, pagina_no_autorizada)
    return app
