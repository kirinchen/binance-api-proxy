from rest.poxy_controller import get_flask_app
import logging

app = get_flask_app()

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    handlers=[logging.FileHandler('/tmp/srv.log', 'w', 'utf-8'), ])
logging.info('So should this')
print('logger is setting')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9282, threaded=True)
