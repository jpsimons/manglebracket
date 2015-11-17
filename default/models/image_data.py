from google.appengine.ext import db
from models import workspace

class ImageData(db.Model):
    workspace = db.ReferenceProperty(workspace.Workspace, required=True)
    filename = db.StringProperty()
    original_filename = db.StringProperty()
    data = db.BlobProperty()
