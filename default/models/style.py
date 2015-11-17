import re
from google.appengine.ext import db
from models.workspace import Workspace
from xml.dom import minidom
import re

class Style(db.Model):
    workspace = db.ReferenceProperty(Workspace, required=True)
    name = db.StringProperty(required=True)
    display_name = db.StringProperty()
    category = db.StringProperty(required=True)
    element = db.StringProperty()
    css_class = db.StringProperty()
    style = db.StringProperty()
    
    border_top = db.BooleanProperty(default=False)
    border_bottom = db.BooleanProperty(default=False)
    font_weight = db.StringProperty()
    font_style = db.StringProperty()
    font_size = db.IntegerProperty()
    margin_left = db.BooleanProperty(default=False)
    list_style_bullet = db.BooleanProperty(default=False)
    list_style_number = db.BooleanProperty(default=False)
    text_position = db.StringProperty()
    text_underline_style = db.StringProperty()
    
    def create_node(self, document, default_element):
        if self.element == "nothing":
            return None
        return document.createElement(self.element or default_element)
        
    def apply(self, node):
        if node.nodeType != minidom.Node.ELEMENT_NODE:
            return
        if self.element:
            node.tagName = self.element
        if self.css_class:
            if node.hasAttribute("class"):
                node.setAttribute("class", node.getAttribute("class") + " " + self.css_class)
            else:
                node.setAttribute("class", self.css_class)
        if self.style:
            if node.hasAttribute("style"):
                s = node.getAttribute("style")
                if not re.search(r";\s*$", s):
                    s += ";"
                s += self.style
                node.setAttribute("style", s)
            else:
                node.setAttribute("style", self.style)
    

    