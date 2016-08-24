from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext


__version__ = '0.1.0'

logger = logging.getLogger(__name__)

class Extension(ext.Extension):

    dist_name = 'HearThisAt'
    ext_name = 'hearthisat'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()        
        schema['email'] = config.String(optional=False)
        schema['password'] = config.Secret(optional=False)
        return schema

    def setup(self, registry):        
        from .hearthisat import HearThisAtBackend
        registry.add('backend', HearThisAtBackend)