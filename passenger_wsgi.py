from a2wsgi import ASGIMiddleware
from app.main import app

# Create the WSGI application
application = ASGIMiddleware(app)
