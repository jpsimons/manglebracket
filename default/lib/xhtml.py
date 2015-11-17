# -*- coding: utf-8 -*-
import re, logging
from xml.dom import minidom

class ElementConverter(object):
    def __init__(self, wk, document, target):
        self.wk = wk
        self.document = document
        self.target = target
        self.style_hash = wk.style_hash()
        
    def _getText(self, node):
        accumulator = ""
        for child in node.childNodes:
            if child.nodeType == minidom.Node.TEXT_NODE:
                accumulator += child.data
            elif child.nodeType == minidom.Node.ELEMENT_NODE:
                accumulator += self._getText(child)
        return accumulator
        
    def convert(self, node):
        
        def has(node_or_list, attribute):
            n = node_or_list[0] if type(node_or_list) == list else node_or_list
            if n.nodeType != minidom.Node.ELEMENT_NODE:
                return False
            else:
                return n.hasAttribute(attribute)
        def get(node_or_list, attribute):
            n = node_or_list[0] if type(node_or_list) == list else node_or_list
            return n.getAttribute(attribute)
        def set(node_or_list, attribute, value):
            if type(node_or_list) == list:
                node_or_list[0].setAttribute(attribute, value)
            else:
                node_or_list.setAttribute(attribute, value)
                
        if node.tagName.startswith("_"):
            return [None, None, None]
        
        methodName = node.tagName.replace("-", "_")
        
        if hasattr(self, methodName):
            styles_in_effect = []
            style = None
            if node.hasAttribute("style-name"):
                if node.getAttribute("style-name") in self.style_hash:
                    style = self.style_hash[node.getAttribute("style-name")]
                
            before, current, after = getattr(self, methodName)(node, style)

            mangle_style = None
            if current and has(current, "mangle-recover"):
                mangle_style = self.style_hash[get(current, "mangle-recover")]
            if mangle_style: styles_in_effect.append(mangle_style)
            if style: styles_in_effect.append(style)
            
            current_root = None
            if current:
                current_root = current[0] if type(current) == list else current
            
            if current_root and node.hasAttribute("style-name"):
                current_root.setAttribute("style-name", node.getAttribute("style-name"))
                
            if current_root:
                for style in styles_in_effect:
                    style.apply(current_root)
            return [before, current, after]
        else:
            return [None, None, None]
    
    def p(self, node, style):
        before = None
        current = None
        after = None
        
        header = False
        blockquote = False
        
        if self.wk.paragraph_borders_to_hr and style:
            if style.border_top:
                before = self.style_hash["MANGLERULE"].create_node(self.document, "hr")
                if before:
                    before.setAttribute("mangle-recover", "MANGLERULE")
            if style.border_bottom:
                after = self.style_hash["MANGLERULE"].create_node(self.document, "hr")
                if after:
                    after.setAttribute("mangle-recover", "MANGLERULE")
                
        if self.wk.auto_header_short_paragraph:
            threshold = self.wk.auto_header_short_paragraph_length
            length = len(self._getText(node))
            header = header or (length < threshold and length > 0)
          
        if self.wk.auto_header_bold_paragraph and style:
            header = header or (style.font_weight == "bold" and len(self._getText(node)) > 0)

        if self.wk.auto_header_caps_paragraph:
            header = header or self._getText(node).isupper()
        
        if self.wk.auto_header_large_font_paragraph and style:
            if style.font_size and style.font_size >= self.wk.auto_header_large_font_paragraph_points:
                header = True

        if self.wk.auto_blockquote and style and style.margin_left:
            blockquote = True

        if header:
            h_style = self.style_hash["MANGLEHEADING"]
            current = self.document.createElement(h_style.element or "h1")
            if h_style.css_class: current.setAttribute("class", h_style.css_class)
            if h_style.style: current.setAttribute("style", h_style.style)
            current.setAttribute("mangle-recover", "MANGLEHEADING")
        elif blockquote:
            b_style = self.style_hash["MANGLEINDENT"]
            current = self.document.createElement(b_style.element or "blockquote")
            if b_style.css_class: current.setAttribute("class", b_style.css_class)
            if b_style.style: current.setAttribute("style", b_style.style)
            current.setAttribute("mangle-recover", "MANGLEINDENT")
        else:
            current = self.document.createElement("p")
        
        return [before, current, after]
        
    def h(self, node, style):
        before_node = None
        if node.hasAttribute("mangle-toc"):
            a_style = self.style_hash["MANGLEANCHOR"]
            before_node = self.document.createElement(a_style.element or "a")
            before_node.setAttribute("name", node.getAttribute("mangle-toc"))
            if a_style.css_class: before_node.setAttribute("class", a_style.css_class)
            if a_style.style: before_node.setAttribute("style", a_style.style)
            before_node.setAttribute("mangle-recover", "MANGLEANCHOR")    
        return_node = self.document.createElement("h" + (node.getAttribute("outline-level") or "1")) # text:outline-level
        return [before_node, return_node, None]

    def list(self, node, style):
        if style and style.list_style_number:
            return_node = self.document.createElement("ol")
        else:
            return_node = self.document.createElement("ul")
        return [None, return_node, None]

    def list_item(self, node, style):
        return [None, self.document.createElement("li"), None]

    def span(self, node, style):
        elements = []
        if style:
            if style and style.font_weight == "bold":
                if self.wk.em_strong: 
                    elements.append(self.document.createElement("strong"))
                else: 
                    elements.append(self.document.createElement("b"))
            if style and style.font_style == "italic":
                if self.wk.em_strong: 
                    elements.append(self.document.createElement("em"))
                else: 
                    elements.append(self.document.createElement("i"))
            if style.text_underline_style:
                elements.append(self.document.createElement("u"))
            if style and style.text_position and style.text_position.find("super") != 1:
                elements.append(self.document.createElement("sup"))
            if not len(elements):
                elements.append(self.document.createElement("burrow"))
        return [None, elements, None]

    def line_break(self, node, style):
        return [None, self.document.createElement("br"), None]

    def a(self, node, style):
        index = int(node.getAttribute("mangle-link-index"))
        #link = self.wk.link_set.filter("index =", ).get()
        link = self.wk.link_array()[index]
        return_node = self.style_hash["MANGLELINK"].create_node(self.document, "a")
        if return_node:
            return_node.setAttribute("href", link.href)
            if not link.href.startswith("#") and (link.external or self.target == "preview"):
                return_node.setAttribute("target", "_blank")
            return_node.setAttribute("mangle-recover", "MANGLELINK")
        
        # href = link.href
        # outline = href.match(/(^#\d+(\.\d+)*).*|outline$/)
        # if outline
        #   href = outline[1]
        # end

        return [None, return_node, None]

    def tab(self, node, style):
        return_node = None
        if self.wk.tab_conversion == "br":
            return_node = self.document.createElement("br")
        elif self.wk.tab_conversion == "space":
            return_node = self.document.createTextNode(" ")
        return [None, return_node, None]

    def bookmark(self, node, style):
        a = self.style_hash["MANGLEANCHOR"].create_node(self.document, "a")
        if a:
            a.setAttribute("name", node.getAttribute("name"))
            a.setAttribute("mangle-recover", "MANGLEANCHOR")
        return [None, a, None]
        
    def bookmark_start(self, node, style):
        before_node = self.style_hash["MANGLEANCHOR"].create_node(self.document, "a")
        if before_node:
            before_node.setAttribute("name", node.getAttribute("name"))
            before_node.setAttribute("mangle-recover", "MANGLEANCHOR")
        return [before_node, self.document.createElement("burrow"), None]

    def image(self, node, style):
        img_style = self.style_hash["MANGLEIMAGE"]
        return_node = self.document.createElement("img")
        img_style.apply(return_node)
        
        img = self.wk.image_set.filter("index =", int(node.getAttribute("mangle-image-index"))).get()
        if img.use_external_url:
            return_node.setAttribute("src", img.external_url)
        else:
            if self.target == "preview":
                return_node.setAttribute("src", "/image/" + str(self.wk.key().id()) + "/" + img.original_filename)
            else:
                return_node.setAttribute("src", self.wk.embedded_image_path + img.data.filename)
        if img.alt:
            return_node.setAttribute("alt", img.alt)
        return_node.setAttribute("mangle-recover", "MANGLEIMAGE")
        return [None, return_node, None]

    def table(self, node, style):
        return [None, self.document.createElement("table"), None]

    def table_row(self, node, style):
        return [None, self.document.createElement("tr"), None]

    def table_cell(self, node, style):
        return [None, self.document.createElement("td"), None]

block_elements = [
  "div", "p", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6", "h7", "hr", "blockquote", "table", "tr", "td", "th"
]
self_closing = [ "br", "hr", "img" ]

span_elements = [ "span", "b", "i", "u", "strong", "em", "sup", "sub" ]

# Close mode is one of { :open, :close, :self_closing }
def to_html_s(child, template, close_mode):
    output = "<"
    output += "/" * (close_mode == "close")
    output += child.tagName
    if close_mode != "close":
        for k in child.attributes.keys():
            a = child.getAttribute(k)
            if k != "style-name" and k != "mangle-recover":
                output += " %s=\"%s\"" % (k, a.replace("\"", "&quot;"))
    if close_mode == "self_closing" and template.output_format == "xhtml":
        output += " /"
    output += ">"
    return output
    
def expand_annotations(s):
    s = re.sub(u"\x02", "<", s)
    s = re.sub(u"\x03", ">", s)
    s = re.sub(u"\x01", "<", s)
    s = re.sub(u"\x04", ">", s)
    return s
    
def recurse(xhtml, writer, target, wk):
    annotate = (target == "code" or target == "preview")
    for child in xhtml.childNodes:

        if child.nodeType == minidom.Node.TEXT_NODE:
            writer.append_text(unicode(child.data))
        elif child.nodeType == minidom.Node.ELEMENT_NODE:
            if child.tagName != "nothing":
                burrow = child.tagName == "p" and xhtml.tagName in ["li", "td", "th"] or child.tagName == "burrow"
                block = child.tagName in block_elements
                annotate_element = "div" if block and target == "preview" else "span"

                if annotate:
                    if child.hasAttribute("style-name"):
                        s = child.getAttribute("style-name")
                        #event = "dblclick" if target == "preview" else "click"
                        writer.append_annotation("<%s class='mgbkt_highlight mgbkt_highlight_clickable mgbkt_style_%s' title='%s'>" % (annotate_element, s, s))
          
                    if child.hasAttribute("mangle-recover"):
                        m = child.getAttribute("mangle-recover")
                        writer.append_annotation("<%s class='mgbkt_highlight mgbkt_style_%s'>" % (annotate_element, m))

                if not len(child.childNodes) and child.tagName in self_closing:
                    writer.append_inline_tag(to_html_s(child, wk, "self_closing"))
                    if child.tagName == "br" and wk.hard_wrap_after_br:
                        writer.append_line_break()
                else:
                    if not burrow:
                        if block:
                            writer.append_block_start(to_html_s(child, wk, "open"))
                        else:
                            writer.append_inline_tag(to_html_s(child, wk, "open"))

                    recurse(child, writer, target, wk)

                    if not burrow:
                        if block:
                            writer.append_block_end(to_html_s(child, wk, "close"))
                        else:
                            writer.append_inline_tag(to_html_s(child, wk, "close"))

                if annotate:
                    if child.hasAttribute("mangle-recover"):
                        writer.append_annotation("</%s>" % annotate_element)
                    if child.hasAttribute("style-name"):
                        writer.append_annotation("</%s>" % annotate_element)

def build_xhtml_tree_recurse(converter, odt_node, xhtml_node):
    for child in odt_node.childNodes:
        if child.nodeType == minidom.Node.TEXT_NODE:
            xhtml_node.appendChild(converter.document.createTextNode(child.data))
        elif child.nodeType == minidom.Node.ELEMENT_NODE:
            xhtml_child = None
            tagName = child.tagName
            if ":" in tagName:
                tagName = tagName.split(":")[1]
            methodName = tagName.replace("-", "_")

            before, current, after = converter.convert(child)
            if before: xhtml_node.appendChild(before)
            if current:
                if type(current) is list:
                    n = xhtml_node
                    for element in current:
                        n.appendChild(element)
                        n = element
                    current = n
                else:
                    xhtml_node.appendChild(current)
                    
            if current and current.nodeType == minidom.Node.TEXT_NODE:
                # Element got downgraded to text. Stop recursing.
                pass
            else:
                build_xhtml_tree_recurse(converter, child, current or xhtml_node)
            if after: xhtml_node.appendChild(after)
               
 
def strip_blank_elements(n):
    for c in [x for x in n.childNodes if x.nodeType == minidom.Node.ELEMENT_NODE]:
        strip_blank_elements(c)

    if n.nodeType == minidom.Node.ELEMENT_NODE:
        if len(n.childNodes) == 0:
            anchor = n.tagName == "a" and n.hasAttribute("name")
            mangle_rule = n.hasAttribute("mangle-recover") and n.getAttribute("mangle-recover") == "MANGLERULE"
            if not anchor and not mangle_rule and not n.tagName in self_closing:
                n.parentNode.removeChild(n)
        
def join_consecutive_paragraphs(n, document):
    for c in [x for x in n.childNodes if x.nodeType == minidom.Node.ELEMENT_NODE]:
        join_consecutive_paragraphs(c, document)

    prev = n.previousSibling
    if prev and prev.nodeType == minidom.Node.ELEMENT_NODE and n.tagName == "p" and prev.tagName == "p":
        if len(n.childNodes) and len(prev.childNodes):
            prev.appendChild(document.createElement("br"))
            for c in n.childNodes:
                prev.appendChild(c.cloneNode(True))
            n.parentNode.removeChild(n)

# Leaf to trunk to leaf again, for a thorough scrubbing
def dedupe(n, document):
    # Recurse
    for c in [x for x in n.childNodes if x.nodeType == minidom.Node.ELEMENT_NODE]:
        dedupe(c, document)

    # Merge duplicate children
    prev = n.previousSibling
    if prev and prev.nodeType == minidom.Node.ELEMENT_NODE and n.tagName == prev.tagName:
        if n.tagName in span_elements:
            for c in n.childNodes:
                prev.appendChild(c.cloneNode(True))
            n.parentNode.removeChild(n)
    
    # Merge duplicate child
    if len(n.childNodes) == 1 and n.childNodes[0].nodeType == minidom.Node.ELEMENT_NODE:
        if n.tagName == n.childNodes[0].tagName and n.tagName in span_elements:
            dupe = n.childNodes[0]
            for c in dupe.childNodes:
                n.appendChild(c.cloneNode(True))
            n.removeChild(dupe)         
    
    # Recurse again
    for c in [x for x in n.childNodes if x.nodeType == minidom.Node.ELEMENT_NODE]:
        dedupe(c, document)
            
def parse(xml, wk, target):
    html = minidom.getDOMImplementation().createDocument(None, "html", None)
    converter = ElementConverter(wk, html, target)
    build_xhtml_tree_recurse(converter, xml.documentElement, html.documentElement)
    if wk.join_consecutive_paragraphs:
       join_consecutive_paragraphs(html.documentElement, html)
    strip_blank_elements(html.documentElement)
    dedupe(html.documentElement, html)
    return html
