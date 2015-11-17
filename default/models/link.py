from google.appengine.ext import db
from models.workspace import Workspace

class Link(db.Model):
    index = db.IntegerProperty()
    href = db.StringProperty(default="")
    original_href = db.StringProperty()
    text = db.StringProperty(default="")
    external = db.BooleanProperty(required=True, default=False)
    workspace = db.ReferenceProperty(Workspace)