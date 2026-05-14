from di.container import Container
from web.module.game_module import create_app


def main():
    app.run(host="0.0.0.0", port=5001, use_reloader=False, threaded=True)


def create_flask_app():
    container = Container()
    return create_app(container)


app = create_flask_app()


if __name__ == "__main__":
    main()
