from apininja.controllers import Controller
from apininja.log import log
from apininja.actions import *
import os, time
import mimetypes
import email.utils

if not mimetypes.inited:
    mimetypes.init()


class RedirectSecureController(Controller):
    def execute(self):
        uri = self.request.uri
        proto = self.scheme
        secure = self.context.endpoint.secure_protocol
        uri.scheme = secure
        location = str(uri)
        self.response.redirect(location)
        