import os
from app import app

if __name__ == '__main__':
    os.environ.setdefault('FLASK_ENV', 'development')
    app.run(host='0.0.0.0', port=5000, debug=True)
