from google.appengine.ext import db
from models import workspace, image_data

class Image(db.Model):
    workspace = db.ReferenceProperty(workspace.Workspace, required=True)    
    index = db.IntegerProperty()
    original_filename = db.StringProperty()
    external_url = db.StringProperty(default="")
    use_external_url = db.BooleanProperty(default=False)
    alt = db.StringProperty(default="")
    data = db.ReferenceProperty(image_data.ImageData, required=True)
    
    def one_based_index(self):
        return self.index + 1