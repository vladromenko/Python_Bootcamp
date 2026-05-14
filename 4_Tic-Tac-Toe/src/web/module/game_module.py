from flask import Flask

from di.container import Container
from web.route.game_route import create_game_blueprint


def create_app(container: Container) -> Flask:
    app = Flask(__name__)
    app.register_blueprint(create_game_blueprint(container))
    return app
