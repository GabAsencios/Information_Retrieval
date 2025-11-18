from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import os


class SpectrumSpider(CrawlSpider):
    name = 'spectrum'
    allowed_domains = ['spectrum.library.concordia.ca']
    start_urls = ['https://spectrum.library.concordia.ca']

    pdf_count = 0

    custom_settings = {
        'ITEM_PIPELINES': {
            'scrapy.pipelines.files.FilesPipeline': 1,
        },
        'FILES_STORE': os.path.join(os.path.dirname(__file__), 'Thesis'),
        'CLOSESPIDER_ITEMCOUNT': 10,
        'LOG_LEVEL': 'DEBUG',  # See what's happening
    }

    rules = (
        Rule(LinkExtractor(allow=r'^https://spectrum\.library\.concordia\.ca/browse\.html$'), follow=True),
        Rule(LinkExtractor(allow=r'^https://spectrum\.library\.concordia\.ca/view/doctype/$'), follow=True),
        Rule(LinkExtractor(allow=r'^https://spectrum\.library\.concordia\.ca/view/doctype/thesis/$'), follow=True),
        Rule(LinkExtractor(allow=r'^https://spectrum\.library\.concordia\.ca/view/doctype/thesis/2025\.html$'),
             follow=True),
        Rule(
            LinkExtractor(allow=r'^https://spectrum\.library\.concordia\.ca/id/eprint/\d+/$'),
            callback='parse_thesis_detail',
            follow=True
        ),
    )

    def parse_thesis_detail(self, response):
        self.logger.info(f"Parsing thesis page: {response.url}")

        if self.pdf_count >= 10:
            self.logger.info("Already have 10 PDFs, stopping")
            return

        pdf_link = response.css('a.ep_document_link::attr(href)').get()

        self.logger.info(f"Found PDF link: {pdf_link}")

        if pdf_link:
            self.pdf_count += 1
            self.logger.info(f"Downloading PDF #{self.pdf_count}: {pdf_link}")
            yield {'file_urls': [response.urljoin(pdf_link)]}