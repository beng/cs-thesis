import gevent.monkey
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()

from gor0x import create_app


if __name__ == "__main__":
    app = create_app()
    http_server = WSGIServer(('0.0.0.0', 8888), app)
    http_server.serve_forever()
