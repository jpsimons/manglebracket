import re
from xml.dom import minidom
import xhtml
from models.style import Style
from models.link import Link
from models import image, image_data
from google.appengine.ext import db
import logging

def strip_xml_tree_recurse(original_node, clean_node):
    for child in original_node.childNodes:
        if child.nodeType == minidom.Node.TEXT_NODE:
            clean_node.appendChild(child.cloneNode(False))
        elif child.nodeType == minidom.Node.ELEMENT_NODE:
            clean_child = None
            tagName = child.tagName
            if ":" in tagName:
                tagName = tagName.split(":")[1]
            methodName = tagName.replace("-", "_")
            if hasattr(xhtml.ElementConverter, methodName):
                clean_child = child.cloneNode(False)
                clean_node.appendChild(clean_child)
                strip_xml_tree_recurse(child, clean_child)
            else:
                strip_xml_tree_recurse(child, clean_node)
    
def clean_up_xml(original):
    clean = minidom.getDOMImplementation().createDocument(None, "html", None)
    strip_xml_tree_recurse(original.getElementsByTagName("office:text")[0], clean.documentElement)
    return clean
    
def count_empty_paragraphs(node):
    total = 0
    empty = 0
    if node.tagName == "p":
        total += 1
        if len(node.childNodes) == 0:
            empty_neighbor = False
            for n in [node.previousSibling, node.nextSibling]:
                if n and n.nodeType == minidom.Node.ELEMENT_NODE and n.tagName == "p":
                    if len(n.childNodes) == 0:
                        empty_neighbor = True
            if not empty_neighbor:
                empty += 1
    for c in [x for x in node.childNodes if x.nodeType == minidom.Node.ELEMENT_NODE]:
        t, e = count_empty_paragraphs(c)
        total += t
        empty += e
    return (total, empty)
    
def strip_prefixes(n):
    if n.nodeType == minidom.Node.ELEMENT_NODE:
        if ":" in n.tagName:
            n.tagName = n.tagName.split(":")[1]
        attribs = []
        for i in range(n.attributes.length):
            attribs.append(n.attributes.item(i))
        for a in attribs:
            name = a.localName
            value = a.nodeValue
            n.removeAttribute(a.name)
            n.setAttribute(name, value)
    for c in n.childNodes:
        strip_prefixes(c)
    
def add_toc_anchor_links(xml):
    any_toc = False
    for a in xml.getElementsByTagName("a"): # text:a
        if a.hasAttribute("href"): # xlink:href
            match = re.search(r"(^#\d+(\.\d+)*).*|outline$", a.getAttribute("href"))
            if match:
                any_toc = True
                a.setAttribute("href", match.group(1))
    if any_toc:
        depth = []
        for h in xml.getElementsByTagName("h"): # text:h
            if h.hasAttribute("outline-level"): # text:outline-level
                level = int(h.getAttribute("outline-level")) - 1
                while len(depth) < level + 1 : depth.append(None)
                if depth[level] is None:
                    depth[level] = 1
                else:
                    depth[level] += 1
                while len(depth) > level + 1: depth.pop()
                h.setAttribute("mangle-toc", ".".join([str(x) for x in depth]))
                
def index_links(xml, wk):
    def get_text(node):
        if node.nodeType == minidom.Node.TEXT_NODE:
            return node.data
        elif node.nodeType == minidom.Node.ELEMENT_NODE:
            string = ""
            for c in node.childNodes:
                string += get_text(c)
            return string
        else:
            return ""
                
    links = []
    for a in xml.getElementsByTagName("a"):
        href = ""
        if a.hasAttribute("href"):
            href = a.getAttribute("href").replace("file://", "")
        text = get_text(a)
        index = len(links)
        links.append(Link(parent=wk, workspace=wk, href=href, original_href=href, text=text, index=index))
        a.setAttribute("mangle-link-index", str(index))
    db.put(links)
    
def index_images(xml, wk):
    image_list = []
    for i, node in enumerate(xml.getElementsByTagName("image")):
        original_filename = node.getAttribute("href").split("/")[1]
        data = wk.imagedata_set.filter("original_filename =", original_filename).get()
        img = image.Image(parent=wk, workspace=wk, original_filename=original_filename, index=i, data=data)
        image_list.append(img)
        node.setAttribute("mangle-image-index", str(i))
    db.put(image_list)
                
def add_mangle_styles(wk):
    mangle_styles = [
        Style(parent=wk, workspace=wk, name="MANGLEHEADING", display_name="(Recovered Headings)", category="recovered", element="h1"),
        Style(parent=wk, workspace=wk, name="MANGLEINDENT", display_name="(Indented)", category="recovered", element="blockquote"),
        Style(parent=wk, workspace=wk, name="MANGLELINK", display_name="(Links)", category="recovered", element=None),
        Style(parent=wk, workspace=wk, name="MANGLEANCHOR", display_name="(Anchors)", category="recovered", element=None),
        Style(parent=wk, workspace=wk, name="MANGLERULE", display_name="(Horizontal Rules)", category="recovered", element="hr"),
        Style(parent=wk, workspace=wk, name="MANGLEIMAGE", display_name="(Images)", category="recovered", element=None),
        Style(parent=wk, workspace=wk, name="MANGLETABLE", display_name="(Tables)", category="recovered", element=None)
    ]
    db.put(mangle_styles)

def add_extracted_styles(wk, content_xml, styles_xml):
    # Round up all the styles that exist
    styles = {}
    category_map = {"office:styles":"named", "office:automatic-styles":"automatic"}
    for xml in [content_xml, styles_xml]:
        for category in category_map:
            for style_block in xml.getElementsByTagName(category):
                for s in [x for x in style_block.getElementsByTagName("*") if x.hasAttribute("style:name")]:
                    name = s.getAttribute("style:name")
                    if not name in styles:
                        display_name = s.getAttribute("style:display-name")
                        styleRecord = Style(parent=wk, workspace=wk, name=name, display_name=(display_name or name), category=category_map[category])

                        for p_prop in s.getElementsByTagName("style:paragraph-properties"):
                            styleRecord.border_top = p_prop.hasAttribute("fo:border-top") and p_prop.getAttribute("fo:border-top") != "none"
                            styleRecord.border_bottom = p_prop.hasAttribute("fo:border-bottom") and p_prop.getAttribute("fo:border-bottom") != "none"
                            if p_prop.hasAttribute("fo:margin-left"):
                                match = re.match("\d+", p_prop.getAttribute("fo:margin-left"))
                                if match is not None:
                                    styleRecord.margin_left = match.group(0) and int(match.group(0)) > 0
                        for t_prop in s.getElementsByTagName("style:text-properties"):
                            if t_prop.hasAttribute("fo:font-weight"):
                                styleRecord.font_weight = t_prop.getAttribute("fo:font-weight")
                            if t_prop.hasAttribute("fo:font-style"):
                                styleRecord.font_style = t_prop.getAttribute("fo:font-style")
                            if t_prop.hasAttribute("fo:font-size"):
                                match = re.match(r"(\d+)([a-zA-Z]+)?", t_prop.getAttribute("fo:font-size"))
                                if match:
                                    size = float(match.group(1))
                                    units = match.group(2)
                                    if units == "in": size = size * 72
                                    if units == "cm": size = size * 28
                                    styleRecord.font_size = int(size)
                            if t_prop.hasAttribute("text-position"):
                                styleRecord.text_position = t_prop.getAttribute("text-position")
                            if t_prop.hasAttribute("style:text-underline-style"):
                                styleRecord.text_underline_style = t_prop.getAttribute("style:text-underline-style")
                        styleRecord.list_style_bullet = len(s.getElementsByTagName("text:list-level-style-bullet")) > 0
                        styleRecord.list_style_number = len(s.getElementsByTagName("text:list-level-style-number")) > 0
                        styles[name] = styleRecord        

    styles_in_use = {}
    # Only create the ones that are used
    # for body in content_xml.getElementsByTagName("office:body"):
    #     for el in body.getElementsByTagName("office:text"):
    for el in content_xml.getElementsByTagName("*"):
        if el.hasAttribute("text:style-name"):
            name = el.getAttribute("text:style-name")
            if name in styles and name not in styles_in_use:
                styles_in_use[name] = styles[name]

    db.put([styles_in_use[x] for x in styles_in_use])