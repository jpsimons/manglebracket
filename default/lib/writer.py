# -*- coding: utf-8 -*-
import re
from lib import encoding

def computed_length(s):
    equiv = re.sub("\x02.*?\x03", "", s)
    equiv = re.sub("\x01.*?\x04", "", equiv)
    equiv = equiv.replace("\t", "        ")
    return len(equiv)
    
class Writer(object):
    def __init__(self, workspace):
        self.workspace = workspace
        self.lines = [u""]
        self.indentation = 0
        self.last_type = None
        self.contents_indented = []

    def indent(self):
        if self.indentation == 0:
            return
        if ">" in self.lines[-1]:
            i = self.lines[-1].find(">")
            wrapped = self.lines[-1][i+1:]
            self.lines[-1] = self.lines[-1][0:i+1]
            self.lines.append(self.workspace.indent_string() * self.indentation + wrapped)
            self.contents_indented[-1] = True

    def wrap(self, placeholder=0):
        length = self.workspace.line_length - placeholder
        overflow = self.workspace.hard_wrap and computed_length(self.lines[-1]) > length
        if overflow:
            do_indent = len(self.contents_indented) > 0 and not self.contents_indented[-1] and self.workspace.indent_style == "block"
            if do_indent: self.indent()

            nonwhite = False
            in_tag = False
            in_annotation = False
            last_was_less_than = False
            last_was_start_annotation = False
            i = len(self.lines[-1]) - 1
            
            while i >= 0:
                char = self.lines[-1][i]
                nonwhite = nonwhite or re.match(r"\S", char)
                in_tag = in_tag or (char == '>')
                in_annotation = in_annotation or (char == "\x03" or char == "\x04")

                # break when we found a possible line wrap point. This is actually the character immediately
                # preceeding the break point.

                # Annotations
                #break if last_was_start_annotation || char[0] == 4

                # Butting tags
                # if last_was_less_than and char == ">":
                #     break

                # White space
                if nonwhite and not in_annotation and not in_tag and re.search(r"\s", char):
                    break
                    
                i -= 1
                if not in_annotation:
                    last_was_less_than = (char == "<")

                in_tag = in_tag and (char != '<')
                in_annotation = in_annotation and (char != "\x02" and char != "\x01")
                last_was_start_annotation = (char[0] == "\x02")

            # i is the space character where to break at
            if i >= 0 and len(self.lines[-1][0:i].strip()):
                extra = self.lines[-1][i+1:]
                self.lines[-1] = self.lines[-1][:i+1]
                adjusted_indent = self.indentation
                if self.workspace.indent_style == "inline":
                    adjusted_indent -= 1
                self.lines.append(self.workspace.indent_string() * adjusted_indent + extra)

    def append_block_start(self, string):
        if self.last_type: self.lines.append('')
        self.lines[-1] += (self.workspace.indent_string() * self.indentation)
        self.lines[-1] += string
        self.indentation += 1
        self.last_type = "block_start"
        self.contents_indented.append(False)

    def append_block_end(self, string):
        indented = self.contents_indented[-1] or self.last_type == "block_end"
        if not indented: self.wrap(len(string))
        indented = indented or self.contents_indented[-1]
        if indented:
            self.lines.append(self.workspace.indent_string() * (self.indentation-1) + string)
        else:
            self.lines[-1] += string
        self.last_type = "block_end"
        self.contents_indented.pop()
        self.indentation -= 1

    # Tags can't be broken onto multiple lines
    def append_inline_tag(self, string):
        if self.last_type == "block_end":
            self.lines.append(self.workspace.indent_string() * self.indentation)
        elif self.last_type == "break":
            if self.workspace.indent_style == "block":
                if not self.contents_indented[-1]: self.indent()
            indent_adjustment = -1 if self.workspace.indent_style == "inline" else 0
            self.lines.append(self.workspace.indent_string() * (self.indentation + indent_adjustment))
        self.lines[-1] += string
        self.last_type = "inline_tag"
        self.wrap()

    # Text can be hard-wrapped
    def append_text(self, string):
        # XML-safe
        string = string.replace("&", "&amp;")
        # SGML-safe
        string = string.replace("<", "&lt;").replace(">", "&gt;")
        # Straighten curly quotes
        if self.workspace.straighten_curly_quotes:
          string = string.replace(u"“", "\"").replace(u"”", "\"").replace(u"’", "'").replace(u"‘", "'")
        # Encode
        string = encoding.encode_html(string, self.workspace.encoding)

        if self.workspace.smarty_pants:
            string = string.replace("--", u"—").replace("...", u"…")
            string = re.sub(r"\b'", u"’", string)
            string = re.sub(r"'\b", u"‘", string)
            string = re.sub(r"\B'\B", u"‘", string)
            string = re.sub(r"\b\"", u"”", string)
            string = re.sub(r"\"\b", u"“", string)
        if self.last_type == "block_end":
            self.lines.append(self.workspace.indent_string() * self.indentation)
        elif self.last_type == "break":
            if self.workspace.indent_style == "block":
                if not self.contents_indented[-1]: self.indent()
            indent_adjustment = -1 if self.workspace.indent_style == "inline" else 0
            self.lines.append(self.workspace.indent_string() * (self.indentation + indent_adjustment))

        lpad = re.match(r"\s", string)
        if lpad: self.lines[-1] += " "
        for i, word in enumerate(string.split()):
            if i > 0:
                self.lines[-1] += " "
            self.lines[-1] += word
            self.wrap()
        if re.search(r"\s$", string):
            self.lines[-1] += " "
        self.last_type = "text"


    def append_annotation(self, string):
        isopen = string[1] != "/"
        if isopen:
          string = string.replace("<", "\x02").replace(">", "\x03")
        else:
          string = string.replace("<", "\x01").replace(">", "\x04")
        self.lines[-1] += string

    def append_line_break(self):
        self.last_type = "break"

    def to_html(self):
        return u"\r\n".join(self.lines)
