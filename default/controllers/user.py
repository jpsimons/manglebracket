from google.appengine.ext import webapp
from google.appengine.api import users
from models.user import User

class CreateUserHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write("huh?")
        
    def post(self):
        user = users.get_current_user()
        if not user:
            self.response.out.write("You got logged out somehow. <a href='/'>Return to Homepage</a>")
        else:
            user_record = User.all().filter("google_id =", user.user_id()).get()
            if not user_record:
                user_record = User(email=user.email(), google_id=user.user_id())
                user_record.put()
            if self.request.get("google_callback"):
                self.redirect(self.request.get("google_callback"))
            else:
                self.redirect("/documents")
