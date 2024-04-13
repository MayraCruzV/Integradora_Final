from flask_script import Manager, Server  # modulo para levantar nuestro servidor
from app import inicializar_app  # retorna la app que instanciamos en flask
from config import config

configuracion=config['development']
app = inicializar_app(configuracion)
manager = Manager(app)

manager.add_command('runserver',Server(host='127.0.0.1', port=5000))

if __name__ == '__main__':
    manager.run()
