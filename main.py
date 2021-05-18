from datetime import datetime

from rest.poxy_controller import get_flask_app
import logging

app = get_flask_app()

fh = logging.FileHandler('/tmp/{:%Y-%m-%d}.log'.format(datetime.now()), 'w', 'utf-8')
formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(lineno)04d | %(message)s')
fh.setFormatter(formatter)

logging.basicConfig(level=logging.WARNING,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M',
                    handlers=[fh, ])
logging.info('So should this')
print('logger is setting')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9282, threaded=True)
