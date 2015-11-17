from google.appengine.ext import webapp
from google.appengine.api import users
from Cheetah.Template import Template
from google.appengine.ext import db

class AboutHandler(webapp.RequestHandler):
    def get(self):
        template = Template(file="templates/about.html")
        self.response.out.write(template)

class SupportHandler(webapp.RequestHandler):
    def get(self):
        template = Template(file="templates/support.html")
        self.response.out.write(template)
        
class IndexHandler(webapp.RequestHandler):
    def get(self):
        template = Template(file="templates/index.html")
        template.user = users.get_current_user()
        template.login_url = users.create_login_url(self.request.uri)
        template.logout_url = users.create_logout_url("/")
        self.response.out.write(template)