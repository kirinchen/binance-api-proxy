from rest.poxy_controller import get_flask_app

app = get_flask_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9282, threaded=True)
