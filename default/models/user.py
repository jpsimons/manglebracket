from google.appengine.ext import db

class User(db.Model):
    google_id = db.StringProperty()
    open_id = db.StringProperty()
    email = db.StringProperty(required=True)
    anonymous = db.BooleanProperty(default=False)