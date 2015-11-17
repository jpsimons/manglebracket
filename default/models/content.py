from google.appengine.ext import db
from google.appengine.api import memcache
import pickle, logging
from xml.dom import minidom

def find(id):
    key = "content_" + str(id)
    data = memcache.get(key)
    if data is not None:
        return minidom.parseString(data)
    content = Content.get_by_id(int(id))
    memcache.set(key, content.xml)
    return content
    
class Content(db.Model):
    xml = db.BlobProperty()
