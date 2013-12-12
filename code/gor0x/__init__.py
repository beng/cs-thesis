from flask import Flask, render_template
from flask.ext.assets import Environment, Bundle

from .server.views import mod as main_blueprint

assets = Environment()


def create_app():
    app = Flask(__name__)
    app.config.from_object('gor0x.settings.config')

    # register blueprints
    app.register_blueprint(main_blueprint)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html')

    @app.errorhandler(500)
    def internal_error(exception):
        # app.logger.exception(exception)
        return "Some Internal error has taken place."

    assets.init_app(app)

    js = Bundle('js/*')
    assets.register('js_all', js)

    return app
