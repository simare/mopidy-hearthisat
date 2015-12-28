from __future__ import unicode_literals
import json
import pykka
import logging

from urllib import quote_plus

from mopidy import backend, models
from mopidy.models import Album, Artist, Track, Ref, SearchResult


from requests import Session, exceptions
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

class HearThisAtBackend(pykka.ThreadingActor, backend.Backend):
	uri_schemes = ['hearthisat']
	
	def __init__(self, config, audio):
		super(HearThisAtBackend, self).__init__()		
		self.audio = audio
		self.library = HearThisAtLibrary(backend=self)
		self.hearthisat = Client()

class HearThisAtLibrary(backend.LibraryProvider):
	root_directory = Ref.directory(uri='hearthisat:root:', name='HEARTHIS.AT')

	def browse(self, uri):
		result = []
		logger.info('mopidy uri %s', uri)
		schema, content_type, content_uri = uri.split(':')		
		if content_type == 'root':
			result = self.backend.hearthisat.categories()
		if content_type == 'categories':	
			result = self.backend.hearthisat.category_list(content_uri)
		if content_type == 'track':
			result = self.backend.hearthisat.track(content_uri)
		
		return result

	def lookup(self, uri):
		result = []
		logger.info('lookup %s', uri)
		uri = uri.split(':')		
		result.append(self.backend.hearthisat.track(uri[-2] +':'+ uri[-1]))
		return result

class Client(object):
	def __init__(self):
		self._base_uri = 'https://api-v2.hearthis.at/'
		self._session = Session()        
        #self._session.headers['User-Agent'] = ' '.join(['Mopidy-HearThisAt/%s' % '0.1.0', 'Mopidy/%s' % '1.1.1', self._session.headers['User-Agent']])
        #self._session.mount(self._base_uri, HTTPAdapter(max_retries=3))

	def categories(self, uri='categories'):
		return self._request(uri, self._directory_wrapper)

	def category_list(self, category_uri):
		result = []
		page = 1
		uri = 'categories/'+category_uri+'?page=1&count=20'		
		
		result = self._request(uri, self._track_ref_wrapper)
		# while res:
		# 	page+=1
		# 	uri = 'categories/'+category_uri+'?page=%s&count=20'%page			
		# 	res = self._request(uri, self._track_ref_wrapper)
		# 	result = res + result
		# 	yield result
		return result

	def track(self, uri):		
		return self._request(uri, self._track_wrapper)

	def _track_wrapper(self, elem):
		logger.debug(elem)
		return Track(
			uri=elem[u'stream_url'], 
			name=elem[u'title'], 
			length=(int(elem[u'duration'])*1000),
			genre=elem[u'genre'],
			artists=[Artist(uri=elem[u'user'][u'uri'], name=elem[u'user'][u'username'])]
			)

	def _directory_wrapper(self, elem):
		return Ref.directory(uri='hearthisat:categories:' + elem[u'id'], name=elem[u'name'])

	def _track_ref_wrapper(self, elem):
		return Ref.track(uri='hearthisat:track:' + elem[u'uri'], name=elem[u'title'])

	def _request(self, uri, result_wrapper):
		if not uri:
			uri = 'categories'
		if self._base_uri not in uri:
			uri = self._base_uri + uri
		logger.info('request uri %s', uri)
		result = []
		try:
			resp = self._session.get(uri)
			if resp.status_code == 200:				
				data = json.loads(resp.text)
				logger.debug('data %s ', data)
				if not isinstance(data, list):
					return result_wrapper(data)
				else:
					for elem in data:					
						result.append(result_wrapper(elem))
			return result
		except exceptions.RequestException as e:
			logger.error('Fetch failed %s', e)
		except ValueError as e:
			logger.error('Fetch failed %s', e)
