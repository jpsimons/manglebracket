from google.appengine.ext import webapp
from google.appengine.api import users
from Cheetah.Template import Template
from models.user import User

class IndexHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            user_record = User.all().filter("google_id =", user.user_id()).get()
            if user_record:
                template = Template(file="templates/documents.html")
                template.logout_url = users.create_logout_url("/")
                template.user = user
                template.user_record = user_record
                self.response.out.write(template)
            else:
                template = Template(file="templates/create_account.html")
                template.user = user
                template.logout_url = users.create_logout_url("/")
                self.response.out.write(template)

class SetupHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.response.out.write("Sorry you got logged out somehow")
        else:
            template = Template(file="templates/create_account_google.html")
            template.user = user
            template.google_callback = self.request.get("callback")
            self.response.out.write(template)
