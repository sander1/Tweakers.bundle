PREFIX = '/video/tweakers'
NAME = 'Tweakers'
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'
BASE_URL = 'https://tweakers.net/video/'
MAIN_URL = BASE_URL + 'zoeken/?'
REVIEW_URL = MAIN_URL + 'i=6&' # i = Video Type filter, 6 is video review id
RE_DATE = Regex("([0-3][0-9]|[0-9])(\/|-|\.)([0-1][0-9]|[0-9])(\/|-|\.)(19[7-9]\d|2\d\d\d)")

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

	HTTP.CacheTime = 300
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'

	# Handle cookies & create session
	HTTP.ClearCookies()

	data = HTTP.Request('https://tweakers.net/', cacheTime=0)
	tnet_id = data.headers['set-cookie'].split('TnetID=.')[-1].split(';')[0]

	return_to = HTML.ElementFromString(data.content).xpath('//input[@name="returnTo"]/@value')[0]
	fragment = HTML.ElementFromString(data.content).xpath('//input[@name="fragment"]/@value')[0]
	tweakers_token = HTML.ElementFromString(data.content).xpath('//input[@name="tweakers_token"]/@value')[0]

	post_values = {
		'decision': 'accept',
		'returnTo': return_to,
		'fragment': fragment,
		'tweakers_token': tweakers_token
	}

	post_headers = {
		'Cookie': 'TnetID=.%s' % (tnet_id)
	}

	headers = HTTP.Request('https://tweakers.net/my.tnet/cookies/', values=post_values, headers=post_headers).headers
	tc = headers['set-cookie'].split('tc=')[-1].split(';')[0]

	HTTP.Headers['Cookie'] = 'TnetID=%s; tc=%s' % (tnet_id, tc)

####################################################################################################
@handler(PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():

	oc = ObjectContainer()
	category = "Categorie\xebn".decode('latin1')

	oc.add(DirectoryObject(
		key = Callback(Videos, title="Video reviews", url=REVIEW_URL),
		title = "Video reviews",
		summary = "Reviews van Tweakers"
	))

	oc.add(DirectoryObject(
		key = Callback(PopulairVideos, title="Populaire video's", url=BASE_URL),
		title = "Populaire video's",
		summary = "Populaire video's" 
	))	

	oc.add(DirectoryObject(
		key = Callback(Filter, title=category, url=MAIN_URL, idKey = 'categoryFilter', filterPrefix = 'c'),
		title = category,
		summary = "Alle %s zoals op de website" % category.lower()
	))

	oc.add(DirectoryObject(
		key = Callback(Filter, title="Onderwerpen", url=MAIN_URL, idKey = 'tweakbaseFilter', filterPrefix = 't'),
		title = "Onderwerpen",
		summary = "Alle onderwerpen zoals op de website"
	))

	oc.add(DirectoryObject(
		key = Callback(Filter, title="Video types", url=MAIN_URL, idKey = 'videoTypesFilter', filterPrefix = 'i'),
		title = "Video types",
		summary = "Alle video types zoals op de website"
	))

	oc.add(DirectoryObject(
		key = Callback(Videos, title="Video archief", url=MAIN_URL),
		title = "Video archief",
		summary = "Alle video van nieuw naar oud"
	))	

	oc.add(DirectoryObject(
		key = Callback(FilterByDateOrKeyword, title="Zoek op datum of trefwoord", url=MAIN_URL),
		title = "Zoek op datum of trefwoord",
		summary = "Zoek op datum of trefwoord"
	))	

	return oc

####################################################################################################
@route(PREFIX + '/videos', page=int, allow_sync=True)
def Videos(title, url, page=1):

	try:
		oc = ObjectContainer(title2=title)
		content = HTML.ElementFromURL(url + 'page=%s' % page )
		table = content.xpath('.//table[contains(@class, "listing useVisitedState")]')[0]

		for video in table.xpath('./tr'):

			path = './td[contains(@class, "video-image")]/a[contains(@class, "thumb video")]/'
			video_url = video.xpath(path + '@href')[0]	
			video_title = video.xpath(path + '@title')[0]
			video_img = video.xpath(path + 'img/@src')[0]

			path = './td/p[@class="lead"]/';
			video_summary = video.xpath(path + 'text()')[0][3:]
			date = video.xpath(path + 'span/text()')[0].lstrip(' ')
			date_now = Datetime.Now()

			if ':' in date:
				video_date = Datetime.ParseDate(date, '%H:%M')
				video_date = video_date.replace(year = date_now.year, month = date_now.month, day = date_now.day)
			elif '\'' in date:
				video_date = Datetime.ParseDate(date, '%m-\'%y')			
			elif not ':' or not '\'' in date:
				date = date + '-%s' % date_now.year
				video_date = Datetime.ParseDate(date, '%d-%m-%y')
			else:
				video_date = date_now

			oc.add(VideoClipObject(
				url = video_url,
				title = video_title,
				summary = video_summary,
				thumb = Resource.ContentsOfURLWithFallback(video_img),
				originally_available_at = video_date
			))

		if len(oc) < 1:
			return ObjectContainer(header="Geen video's", message="Deze directory bevat geen video's")

		if len(content.xpath('//span[@class="pageDistribution"]//a[contains(text(), "Volgende")]')) > 0:

			oc.add(NextPageObject(
				key = Callback(Videos, title=title, url=url, page=page+1),
				title = 'Meer ...'
			))

		return oc

	except:
		return ObjectContainer(header="Geen video's", message="Deze directory bevat geen video's")

####################################################################################################
@route(PREFIX + '/filter', allow_sync=True)
def Filter(title, url, idKey, filterPrefix):

	oc = ObjectContainer(title2=title)

	content = HTML.ElementFromURL(url)
	categoryDiv = content.xpath('.//div[contains(@id, "%s")]/div' % idKey)[0]

 	for video in categoryDiv.xpath('./ul/li'):
		categoryId = video.xpath('./label/span/input/@value')[0]
		categoryName = video.xpath('./label/span[contains (@class, "facetLabel")]/text()')[0]

		video_url = url + '%s=%s&' % (filterPrefix, categoryId)

		oc.add(DirectoryObject(
			key = Callback(Videos, title=categoryName, url=video_url),
			title = categoryName
		))

	oc.objects.sort(key = lambda obj: obj.title)
	return oc

####################################################################################################
@route(PREFIX + '/filterByDateOrKeyword', allow_sync=True)
def FilterByDateOrKeyword(title, url):

	oc = ObjectContainer(title2=title)

	oc.add(InputDirectoryObject(
    	key = Callback(SearchByDate),
    	title = "Zoeken op datum",
    	summary = "Doorzoek alle videos op datum. Zoeken tussen twee datums als volgt:" 
    		+ '\n\n' + "1-1-2014 & 1-1-2015" 
    		+ '\n' + "1/1/2014 & 1/1/2015" 
    		+ '\n' + "1.1.2014 & 1.1.2015"
    		+ '\n' + 'dd-mm-yyyy & dd-mm-yyyy'
    		+ '\n\n\n' + "Zoeken op een specifieke datum:" 
    		+ '\n\n'+ "12-12-2014"
    		+ '\n'+ "dd-mm-yyyy",
    	thumb = R("search-icon.png")
	))

	oc.add(InputDirectoryObject(
    	key = Callback(SearchByKeyword),
    	title = "Zoeken op trefwoord",
    	summary = "Doorzoek alle videos op het ingevulde trefwoord.",
    	thumb = R("search-icon.png")
	))

	return oc

####################################################################################################
@route(PREFIX + '/searchByKeyword')
def SearchByKeyword(query, url = None):

	search_text = query.replace(" ", "%20")
	video_url = MAIN_URL + 'k=%s&' % search_text

	return Videos('Videos', video_url, 1)

####################################################################################################
@route(PREFIX + '/searchByDate')
def SearchByDate(query, url = None):

	result = RE_DATE.findall(query)

	if result:
		if len(result) > 1:
			video_url = MAIN_URL + 'pti=%s&pta=%s&' % (''.join(result[0]), ''.join(result[1]))
		else:
			video_url = MAIN_URL + 'pti=%s&pta=%s&' % (''.join(result[0]), ''.join(result[0]))

		return Videos('Videos', video_url, 1)
	return ObjectContainer(header="Error", message="Er is geen gelidige datum ingevuld.")

####################################################################################################
@route(PREFIX + '/populairVideos', allow_sync=True)
def PopulairVideos(title, url):

	oc = ObjectContainer(title2=title)
	content = HTML.ElementFromURL(url)
	table = content.xpath('.//div[contains(@class, "portalFpaItems portalBlock")]/div')[0]

	for video in table.xpath('./div'):

		path = './a[contains(@class, "fpaTitle")]/'
		video_url = video.xpath(path + '@href')[0]
		video_title = video.xpath(path + 'h2/text()')[0]
		video_summary = video.xpath(path + 'p/text()')[0]

		video_img = video.xpath('./a[contains(@class, "fpaImageContainer")]/div/img/@src')[0]		

		oc.add(VideoClipObject(
			url = video_url,
			title = video_title,
			summary = video_summary,
			thumb = Resource.ContentsOfURLWithFallback(video_img),
		))

	if len(oc) < 1:
		return ObjectContainer(header="Geen video's", message="Deze directory bevat geen video's")

	if len(content.xpath('//span[@class="pageDistribution"]//a[contains(text(), "Volgende")]')) > 0:

		oc.add(NextPageObject(
			key = Callback(Videos, title=title, url=url, page=page+1),
			title = 'Meer ...'
		))

	return oc
