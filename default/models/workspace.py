from google.appengine.ext import db
from google.appengine.api import memcache
import pickle, logging, random
from xml.dom import minidom
import css
from models.content import Content
from models.user import User

def find(id):
    key = "workspace_" + str(id)
    data = memcache.get(key)
    if data is not None:
        return pickle.loads(data)
    workspace = Workspace.get_by_id(int(id))
    logging.info("workspace size: " + str(len(pickle.dumps(workspace))))
    memcache.set(key, pickle.dumps(workspace))
    return workspace
    
indent_strings = [
    ["2 spaces", "  ", "2"],
    ["3 spaces", "   ", "3"],
    ["4 spaces", "    ", "4"],
    ["5 spaces", "     ", "5"],
    ["8 spaces", "        ", "8"],
    ["tab character", "\t", "t"]
]

indent_styles = [
    ["Block indent", "block"],
    ["Hanging indent", "hanging"],
    ["Inline", "inline"]
]

font_sizes = [9, 10, 11, 12, 13, 14, 15, 16, 18]

font_faces = [
    ["default", "Font...", "Consolas,Inconsolata,'Droid Sans Mono','Andale Mono',monospace"],
    ["andale", "Andale Mono", "'Andale Mono', monospace"],
    ["courier", "Courier", "Courier, 'Courier New', monospace"],
    ["lucida", "Lucida Console", "'Lucida Console', monospace"],
    ["monaco", "Monaco", "Monaco, monospace"]
]

encodings = [
    ["utf-8", "UTF-8"],
    ["iso-8859-1", "Latin-1"],
    ["us-ascii", "ASCII"]
]

class Workspace(db.Model):
    user = db.ReferenceProperty(User, required=True)
    original_filename = db.StringProperty(required=True)
    
    content = db.ReferenceProperty(Content, required=False)
    
    # UI preferences
    edit_tab = db.StringProperty(required=True, default="html", choices=set(["html","urls","styles","images","css","output"]))
    view_tab = db.StringProperty(required=True, default="code", choices=set(["code", "preview"]))
    font_size = db.IntegerProperty(required=True, default=13)
    font_face = db.StringProperty(required=True, default="default", choices=set([x[0] for x in font_faces]))
    
    # HTML tab
    join_consecutive_paragraphs = db.BooleanProperty(required=True, default=True)
    auto_blockquote = db.BooleanProperty(required=True, default=True)
    paragraph_borders_to_hr = db.BooleanProperty(required=True, default=True)
    auto_header_large_font_paragraph = db.BooleanProperty(required=True, default=True)
    auto_header_large_font_paragraph_points = db.IntegerProperty(required=True, default=18)
    auto_header_short_paragraph = db.BooleanProperty(required=True, default=False)
    auto_header_short_paragraph_length = db.IntegerProperty(required=True, default=40)
    auto_header_bold_paragraph = db.BooleanProperty(required=True, default=True)
    auto_header_caps_paragraph = db.BooleanProperty(required=True, default=False)
    br_paragraphs = db.BooleanProperty(required=True, default=False)
    em_strong = db.BooleanProperty(required=True, default=False)
    tables_zebra_striped = db.BooleanProperty(required=True, default=True)
    tab_conversion = db.StringProperty(required=True, default="space", choices=set(["space", "br"]))
    
    # Links tab
    base_href = db.StringProperty(default="")
    # link_set is array of links
    
    # Images tab
    embedded_image_path = db.StringProperty(default="")
    
    # CSS
    css = db.TextProperty(default=css.sample_stylesheets[0][1])
    
    # Output
    hard_wrap = db.BooleanProperty(required=True, default=True)
    line_length = db.IntegerProperty(required=True, default=100)
    hard_wrap_after_br = db.BooleanProperty(required=True, default=True)
    indent_string_code = db.StringProperty(required=True, default="3", choices=set([x[2] for x in indent_strings]))
    indent_style = db.StringProperty(required=True, default="block", choices=set([x[1] for x in indent_styles]))
    output_format = db.StringProperty(required=True, default="html", choices=set(["html", "xhtml"]))
    encoding = db.StringProperty(required=True, default=encodings[0][0], choices=set([x[0] for x in encodings]))
    straighten_curly_quotes = db.BooleanProperty(required=True, default=False)
    smarty_pants = db.BooleanProperty(required=True, default=False)
    
    demo = db.BooleanProperty(default=False)
    sharing_key = db.StringProperty(default=str(random.randint(1000000, 1999999)))

    def indent_string(self):
        return [x[1] for x in indent_strings if x[2] == self.indent_string_code][0]

    def font_face_string(self):
        return [x[2] for x in font_faces if x[0] == self.font_face][0]

    def style_hash(self):
        key = "styles_" + str(self.key().id())
        data = memcache.get(key)
        if data is not None:
            return data
        styles = {}
        for style in self.style_set:
            styles[style.name] = style
        memcache.set(key, styles)
        return styles
        
    def invalidate_style_hash(self):
        key = "styles_" + str(self.key().id())
        memcache.delete(key)
        
    def link_array(self):
        key = "links_" + str(self.key().id())
        data = memcache.get(key)
        if data is not None:
            return data
        links = []
        for link in self.link_set.order("index"):
            links.append(link)
        memcache.set(key, links)
        return links
        
    def invalidate_link_array(self):
        key = "links_" + str(self.key().id())
        memcache.delete(key)
        
    def content_xml(self):
        return minidom.parseString(self.content.xml)
        
    def original_extension(self):
        ext = self.original_filename.split(".")[-1]
        if ext in ["odt"]:
            return ext
        return "odt"
        