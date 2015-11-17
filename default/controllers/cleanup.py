from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from models.content import Content
from models.image import Image
from models.image_data import ImageData
from models.link import Link
from models.style import Style
from models.workspace import Workspace

class CleanupHandler(webapp.RequestHandler):
    def get(self):
        counts = {}
        counts["content"] = Content.all(keys_only=True).count()
        counts["image"] = Image.all(keys_only=True).count()
        counts["image_data"] = ImageData.all(keys_only=True).count()
        counts["link"] = Link.all(keys_only=True).count()
        counts["style"] = Style.all(keys_only=True).count()
        counts["workspace"] = Workspace.all(keys_only=True).count()
        self.response.out.write(str(counts) + "<p><form method='POST' action='/cleanup'><input type=submit value='Clean up'></form>")

    def post(self):
        user = users.get_current_user()
        if user and user.nickname() == "coolcucumber":
            # Deletes all Datastore data!!!
            db.delete(Content.all(keys_only=True).fetch(None))
            db.delete(Image.all(keys_only=True).fetch(None))
            db.delete(ImageData.all(keys_only=True).fetch(None))
            db.delete(Link.all(keys_only=True).fetch(None))
            db.delete(Style.all(keys_only=True).fetch(None))
            db.delete(Workspace.all(keys_only=True).fetch(None))
            self.response.out.write("Cleaned up")
        else:
            self.response.out.write("Unauthorized user")

