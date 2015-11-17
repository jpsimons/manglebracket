from google.appengine.ext import webapp
from google.appengine.api import users
from Cheetah.Template import Template
from google.appengine.ext import db
from models.link import Link
from models.workspace import Workspace, Content
from lib.zipfilecopy import ZipFile # Copy of the Python 2.6 standard library "zipfile", GAE's version is crippled
from xml.dom import minidom
from models import workspace, style, css, image_data
from models.user import User
from lib import xhtml, writer, importer, encoding
import os, cgi, re, pickle, logging, StringIO, urllib2
from google.appengine.api import urlfetch

def create_workspace(user_record, data, filename, demo=False):
    # if filename.endswith(".doc") or filename.endswith(".docx"):
    #     result = urlfetch.fetch("http://openoffice.manglebracket.com/upload", method="POST", payload=data, deadline=10, headers={'Content-Type':'raw'})
    #     if result.status_code == 200:
    #         data = result.content
    #     else:
    #         logging.info("Error: %s", str(result.status_code))
    f = StringIO.StringIO(data)
    odt = ZipFile(f)
    content_xml = minidom.parse(odt.open("content.xml"))
    styles_xml = minidom.parse(odt.open("styles.xml"))

    wk = workspace.Workspace(user=user_record, original_filename=filename, demo=demo)
    wk.put()

    image_list = []
    index = 0
    for i in odt.infolist():
        if i.filename.startswith("Pictures/"):
            filename = i.filename.split("/")[1]
            extension = filename.split(".")[-1]
            data = image_data.ImageData(
                parent=wk, 
                workspace=wk,
                filename=str(index+1).zfill(3) + "." + extension,
                original_filename=filename, 
                data=odt.open(i.filename).read()
            )
            image_list.append(data)
            index += 1
    db.put(image_list)

    content = importer.clean_up_xml(content_xml)
    importer.strip_prefixes(content)
    importer.add_toc_anchor_links(content)
    importer.index_links(content, wk)
    importer.index_images(content, wk)
    total_paragraphs, empty_paragraphs = importer.count_empty_paragraphs(content.documentElement)
    logging.info("paragraphs %i/%i" % (empty_paragraphs, total_paragraphs))
    empty_paragraph_ratio = float(empty_paragraphs) / (total_paragraphs + 0.001)
    content_model = Content(parent=wk, xml=content.toxml("utf-8")).put()

    wk.content = content_model
    wk.join_consecutive_paragraphs = (empty_paragraph_ratio > 0.15)
    wk.put()

    importer.add_mangle_styles(wk)
    importer.add_extracted_styles(wk, content_xml, styles_xml)
    return wk
    

class WorkspaceHandler(webapp.RequestHandler):
    """ The full workspace HTML page. """
    def get(self, id):
        nickname = "demo@manglebracket.com"
        wk = Workspace.get_by_id(int(id))
        if not wk:
            self.response.out.write("No such workspace")
            return
        
        user = users.get_current_user()
        if user:
            nickname = user.nickname()
            if wk.user.google_id != user.user_id() and not wk.demo:
                self.response.out.write("Not your workspace, %s" % nickname)
                return
        
        if not user and not wk.demo:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            path = 'templates/workspace.html'
            template = Template(file=path)
            template.user = nickname
            template.logout_url = users.create_logout_url("/")
            template.wk = Workspace.get_by_id(int(id))
            template.id = id
            template.indent_strings = workspace.indent_strings
            template.indent_styles = workspace.indent_styles
            template.font_sizes = workspace.font_sizes
            template.font_faces = workspace.font_faces
            template.encodings = workspace.encodings
            template.sample_stylesheets = css.sample_stylesheets
            self.response.out.write(template)
            
class WorkspaceSubviewHandler(webapp.RequestHandler):
    """ The document in a particular format, for exporting for filling the iframe. """
    def get(self, id, format):
        wk = Workspace.get_by_id(int(id))
        if not wk:
            self.response.out.write("No such workspace")
            return
        
        # Check access
        if self.request.get("key") and wk.sharing_key == self.request.get("key"):
            pass
        elif wk.demo:
            pass
        else:
            user = users.get_current_user()
            if not user or wk.user.google_id != user.user_id():
                self.response.out.write("Not logged in as the right user")
                return
        
        x = xhtml.parse(wk.content_xml(), wk, format)
        w = writer.Writer(wk)
        xhtml.recurse(x.documentElement, w, format, wk)
        html = w.to_html()
        
        # Re-encode the whole thing, in case out-of-range characters were in
        # elements names or attributes.
        html = encoding.encode_html(html, wk.encoding)
        
        if format == "text":
            self.response.headers["Content-Type"] = "text/plain; charset=%s" % wk.encoding
            self.response.out.write(html)
        else:
            path = 'templates/%s.html' % format
            template = Template(file=path)
            template.wk = wk      
            if format == "code": html = cgi.escape(html)
            if format != "text": html = xhtml.expand_annotations(html)
            template.html = html
            template.id = id
            self.response.headers["Content-Type"] = "text/html; charset=%s" % wk.encoding
            if wk.encoding == "utf-8":
                self.response.out.write(unicode(template))
            else:
                self.response.out.write(unicode(template).encode(wk.encoding))

class DemoWorkspaceHandler(webapp.RequestHandler):
    def get(self, filename):
        user_record = None
        user = users.get_current_user()
        if user:
            user_record = User.all().filter("google_id =", user.user_id()).get()
        if not user_record:
            user_record = User.all().filter("email =", "demo@manglebracket.com").get()
        if not user_record:
            user_record = User(email="demo@manglebracket.com", anonymous=True).put()
        
        real_filename = "odt_documents/%s.odt" % filename
        wk = create_workspace(user_record, open(real_filename).read(), "%s.doc" % filename, True)
        self.redirect("/workspace/%i" % wk.key().id())
        
class NewWorkspaceHandler(webapp.RequestHandler):
    """ Creates a new workspace from an OpenDocument ODT file. """
    def get(self):
        self.response.out.write("Missing data")
        
    def post(self):
        user = users.get_current_user()
        if not user:
            self.response.out.write("You got logged out somehow. <a href='/'>Return to homepage</a>")
        else:
            user_record = User.all().filter("google_id =", user.user_id()).get()
            if not user_record:
                self.response.out.write("You haven't signed up yet")
            else:
                filename = self.request.POST["document"].filename
                data = self.request.get("document")
                wk = create_workspace(user_record, data, filename)
                self.redirect("/workspace/%i" % wk.key().id())
        
class UpdateWorkspaceHandler(webapp.RequestHandler):
    def post(self, id, type):
        wk = workspace.Workspace.get_by_id(int(id))
        field = self.request.get("field")
        value = self.request.get("value")
        persist = self.request.get("persist") == "1"
        if (hasattr(wk, field)):
            if type == "bool":
                setattr(wk, field, value == "1")
                wk.put()
            elif type == "int":
                setattr(wk, field, int(value))
                wk.put()
            elif type == "string":
                setattr(wk, field, value)
                wk.put()
        self.response.out.write("OK")
        
class SaveStyleHandler(webapp.RequestHandler):
    def post(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        name = self.request.get("name")
        style = wk.style_set.filter("name =", name).get()
        if style:
            style.element = self.request.get("element")
            style.css_class = self.request.get("css_class")
            style.style = self.request.get("style")
            style.put()
            wk.invalidate_style_hash()
            self.response.out.write("OK")
        else:
            self.response.out.write("Not found")
            
class SaveLinkHandler(webapp.RequestHandler):
    def post(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        link = wk.link_set.filter("index =", int(self.request.get("index"))).get()
        if link:
            link.href = self.request.get("href")
            link.external = (self.request.get("external") == "1")
            link.put()
            wk.invalidate_link_array()
            self.response.out.write("OK")
        else:
            self.response.out.write("Not found")
            
class SaveImageHandler(webapp.RequestHandler):
    def post(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        image = wk.image_set.filter("index =", int(self.request.get("index"))).get()
        if image:
            image.alt = self.request.get("alt")
            image.use_external_url = (self.request.get("use_external_url") == "True")
            image.external_url = self.request.get("external_url")
            image.put()
            self.response.out.write("OK")
        else:
            self.response.out.write("Not found")
            
class SaveEmbeddedImagePathHandler(webapp.RequestHandler):
    def post(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        wk.embedded_image_path = self.request.get("embedded_image_path")
        wk.put()
        self.response.out.write("OK")
        
class DownloadImagesHandler(webapp.RequestHandler):
    def get(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        self.reponse.out.write("OK")
        
class LoadCSSHandler(webapp.RequestHandler):
    def post(self, id):
        wk = workspace.Workspace.get_by_id(int(id))
        field = self.request.get("stylesheet")
        css_text = [x for x in css.sample_stylesheets if x[0] == field][0][1]
        wk.css = css_text
        wk.put()
        self.response.out.write(css_text)
        
class ImageHandler(webapp.RequestHandler):
    def get(self, id, path):
        wk = workspace.Workspace.get_by_id(int(id))
        img = wk.imagedata_set.filter("original_filename =", path).get()
        extension = img.original_filename.split(".")[-1]
        self.response.headers["Content-Type"] = "image/" + extension
        self.response.out.write(img.data)
        