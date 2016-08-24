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
	
	def __init__(self, config, audio):
		super(HearThisAtBackend, self).__init__()
		self.config = config
		self.audio = audio
		self.library = HearThisAtLibrary(backend=self)
		self.playback = HearThisAtPlayback(audio=audio, backend=self)
		self.remote = HearThisAtClient(config=self.config['hearthisat'])
		self.uri_schemes = ['hearthisat']

class HearThisAtPlayback(backend.PlaybackProvider):
	def translate_uri(self, uri):	
		if 'http' in uri:
			playable = uri.split(':')[-1]		
			return 'https:' + playable
		return None



class HearThisAtLibrary(backend.LibraryProvider):
	root_directory = Ref.directory(uri='hearthisat:root:', name='HEARTHIS.AT')

	def __init__(self, *args, **kwargs):
		super(HearThisAtLibrary, self).__init__(*args, **kwargs)
		self.vfs = [Ref.directory(uri='hearthisat:explore:', name='Explore')]
		self.vfs.append(Ref.directory(uri='hearthisat:feed:popular', name='Popular'))
		self.vfs.append(Ref.directory(uri='hearthisat:feed:new', name='New'))
		self.vfs.append(Ref.directory(uri='hearthisat:user:playlists', name='Sets'))		
		self.vfs.append(Ref.directory(uri='hearthisat:user:likes', name='Likes'))
		self.vfs.append(Ref.directory(uri='hearthisat:user:tracks', name='Tracks'))

	def browse(self, uri):
		result = self.vfs
		logger.info('mopidy uri %s', uri)
		schema, content_type, content_uri = uri.split(':')
		if content_type == 'explore':
			result = self.backend.remote.categories()
		if content_type == 'categories':
			result = self.backend.remote.category_list(content_uri)
		if content_type == 'track':
			result = self.backend.remote.track(content_uri)
		if content_type == 'feed':
			result = self.backend.remote.feed(content_uri)
		if content_type == 'user':
			result = self.backend.remote.user_data(content_uri)
		
		return result

	def lookup(self, uri):
		result = []
		logger.info('lookup %s', uri)
		uri = uri.split(':')		
		result.append(self.backend.remote.track(uri[-2] +':'+ uri[-1]))
		return result

	def search(self, query=None, uris=None, exact=False):
		logger.info('search query %s uris %s', query, uris)
		if not query.get('any'):
			return None
		tracks = self.backend.remote.search(query['any'][0])
		return SearchResult(tracks=tracks)

class HearThisAtClient(object):
	def __init__(self, config):		
		logger.info(config)
		self._base_uri = 'https://api-v2.hearthis.at/'
		self._session = Session()
		self.user = self.login(config)
        
	def login(self, config):
		if config['email'] and config['password']:
			query = self._base_uri+'login/?email=%s&password=%s'%(config['email'], config['password'])
			return self._request(query)

	def is_logged_in(self):
		return (self.user is not None) and ('username' in self.user)			

	def user_data(self, content_uri):		
		result = []
		if self.is_logged_in:
			result_wrapper = self._directory_wrapper if content_uri == 'playlists' else self._track_ref_wrapper
			query = self.user['username']+'/?type=%s&page=1&count=20'%content_uri							
			result = self._request(query, result_wrapper)
		return result

	def search(self, query):
		query = 'search?t=%s&page=1&count=20'%(query)
		return self._request(query, self._track_wrapper)

	def feed(self, feed_type):
		query = 'feed?type=%s&page=1&count=20'%feed_type
		return self._request(query, self._track_ref_wrapper)

	def categories(self, uri='categories'):
		return self._request(uri, self._directory_wrapper)

	def category_list(self, category_uri):
		result = []		
		uri = 'categories/'+category_uri+'?page=1&count=20'		
		result = self._request(uri, self._track_ref_wrapper)
		return result

	def track(self, uri):
		logger.info('track %s', uri)		
		return self._request(uri, self._track_wrapper)

	def _artist_wrapper(self, elem):
		return Artist(uri=elem[u'uri'], name=elem[u'username'])

	def _track_wrapper(self, elem):
		logger.debug(elem)
		return Track(
			uri='hearthisat:' + elem[u'stream_url'], 
			name=elem[u'title'], 
			length=(int(elem[u'duration'])*1000),
			genre=elem[u'genre'],
			artists=[self._artist_wrapper(elem[u'user'])]
			)

	def _directory_wrapper(self, elem):
		return Ref.directory(uri='hearthisat:categories:' + elem[u'id'], name=elem[u'name'])

	def _track_ref_wrapper(self, elem):
		return Ref.track(uri='hearthisat:track:' + elem[u'uri'], name=elem[u'title'])

	def _request(self, uri, result_wrapper=(lambda x: x)):
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
