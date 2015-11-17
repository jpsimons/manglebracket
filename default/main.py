#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
import os
from google.appengine.api import users
from Cheetah.Template import Template
from google.appengine.ext import db
from models.link import Link
from models.workspace import Workspace
from xml.dom.minidom import parse
import cgi
from lib import xhtml, writer
from controllers import index, cleanup
from controllers import workspace, documents, user
import pickle
        
def main():
    routes = [
        (r'/about', index.AboutHandler),
        (r'/create_account', user.CreateUserHandler),
        (r'/image/(\d+)/(.*)', workspace.ImageHandler),
        (r'/workspace/(\d+)/download_images', workspace.DownloadImagesHandler),
        (r'/workspace/(\d+)/save_embedded_image_path', workspace.SaveEmbeddedImagePathHandler),
        (r'/workspace/(\d+)/save_image', workspace.SaveImageHandler),
        (r'/workspace/(\d+)/save_link', workspace.SaveLinkHandler),
        (r'/workspace/(\d+)/save_style', workspace.SaveStyleHandler),
        (r'/workspace/(\d+)/update/(\w+)', workspace.UpdateWorkspaceHandler),
        (r'/workspace/(\d+)/loadCSS', workspace.LoadCSSHandler),
        (r'/workspace/new', workspace.NewWorkspaceHandler),
        (r'/create_demo/(\w+)', workspace.DemoWorkspaceHandler),
        (r'/workspace/(\d+)\.(\w+)', workspace.WorkspaceSubviewHandler),
        (r'/workspace/(\d+)', workspace.WorkspaceHandler),
        (r'/support', index.SupportHandler),
        (r'/setup', documents.SetupHandler),
        (r'/documents', documents.IndexHandler),
        (r'/', index.IndexHandler),
		(r'/cleanup', cleanup.CleanupHandler)
    ]
    application = webapp.WSGIApplication(routes, debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
