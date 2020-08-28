import scrapy
from pprint import pprint


class RecommendationsSpider(scrapy.Spider):
    name = 'recommendations'
    start_urls = ['https://www.booksoftitans.com/list']

    def parse(self, response):
        for row in response.xpath('//table[1]//tr'):
            # If this row contains cells
            if row.xpath('./td').extract():
                book = row.xpath('./td[@class="column-1"]/text()').extract_first()
                if not book:
                    book = row.xpath('./td[@class="column-1"]/a/text()').extract_first()
                if book:
                    recommendation = {
                        'book': book,
                        'author': row.xpath('./td[@class="column-2"]/text()').extract_first(),
                        'recommended_by': row.xpath('./td[@class="column-3"]/text()').extract_first(),
                        'podcast_number': int(row.xpath('./td[@class="column-4"]/text()').extract_first())
                    }
                    yield recommendation
