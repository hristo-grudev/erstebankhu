import json

import scrapy

from scrapy.loader import ItemLoader

from ..items import ErstebankhuItem
from itemloaders.processors import TakeFirst

import requests

url = "https://www.erstebank.hu/bin/erstegroup/gemesgapi/feature/gem_site_hu_www-erstebank-hu-hu-es7/,"

base_payload = "{\"filter\":[{\"key\":\"path\",\"value\":\"/content/sites/hu/ebh/www_erstebank_hu/hu/sajto" \
               "/sajtokozlemenyek\"}],\"page\":%s,\"query\":\"*\",\"items\":5,\"sort\":\"DATE_RELEVANCE\"," \
               "\"requiredFields\":[{\"fields\":[\"teasers.NEWS_DEFAULT\",\"teasers.NEWS_ARCHIVE\"," \
               "\"teasers.newsArchive\"]}]} "
headers = {
  'Connection': 'keep-alive',
  'Pragma': 'no-cache',
  'Cache-Control': 'no-cache',
  'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
  'sec-ch-ua-mobile': '?0',
  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
  'Content-Type': 'application/json',
  'Accept': '*/*',
  'Origin': 'https://www.erstebank.hu',
  'Sec-Fetch-Site': 'same-origin',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Dest': 'empty',
  'Referer': 'https://www.erstebank.hu/hu/sajto/sajtokozlemenyek',
  'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8',
  'Cookie': 'TCPID=121311113542745513994; _gid=GA1.2.699402392.1615799642; TC_PRIVACY=0@019@2%2C3@1@1615799744862@; TC_PRIVACY_CENTER=2%2C3; _gcl_au=1.1.1475529929.1615799785; _gat_UA-33280811-1=1; 3cf5c10c8e62ed6f6f7394262fadd5c2=38152618e0350b39d330076005a62c18; _fbp=fb.1.1615799787522.756167059; _ga_PJDMZYN9PZ=GS1.1.1615799637.1.1.1615799840.0; _ga=GA1.2.429937066.1615799642'
}


class ErstebankhuSpider(scrapy.Spider):
	name = 'erstebankhu'
	start_urls = ['https://www.erstebank.hu/hu/sajto/sajtokozlemenyek']
	page = 0

	def parse(self, response):
		payload = base_payload % self.page
		data = requests.request("POST", url, headers=headers, data=payload)
		raw_data = json.loads(data.text)
		for post in raw_data['hits']['hits']:
			link = post['_source']['url']
			date = post['_source']['date']
			title = post['_source']['title']
			yield response.follow(link, self.parse_post, cb_kwargs={'date': date, 'title': title})
		if self.page < raw_data['hits']['total'] // 5:
			self.page += 1
			yield response.follow(response.url, self.parse, dont_filter=True)

	def parse_post(self, response, date, title):
		description = response.xpath(
			'//div[@class="w-auto mw-full rte"]//text()[normalize-space()]').getall()
		description = [p.strip() for p in description]
		description = ' '.join(description).strip()

		item = ItemLoader(item=ErstebankhuItem(), response=response)
		item.default_output_processor = TakeFirst()
		item.add_value('title', title)
		item.add_value('description', description)
		item.add_value('date', date)

		return item.load_item()