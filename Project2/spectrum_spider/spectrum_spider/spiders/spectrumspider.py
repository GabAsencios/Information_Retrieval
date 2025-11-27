import scrapy
import PyPDF2
import io
import json
import os
from scrapy.http import Request, TextResponse
from nltk.stem import PorterStemmer
from collections import Counter
from scrapy.exceptions import CloseSpider


class spectrumspider(scrapy.Spider):
    name = "spectrumspider"
    allowed_domains = ["spectrum.library.concordia.ca"]
    start_urls = ["https://spectrum.library.concordia.ca/"]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Accept max_documents as a spider argument via `-a max_documents=` else no limit
        max_docs_arg = kwargs.get("max_documents", None)
        self.max_documents = int(max_docs_arg) if max_docs_arg else None
        self.document_count = 0
        self.pdf_found = 0

        # SPIMI block variables
        self.inverted_index = {}
        self.block_number = 0
        self.inverted_block = {}
        self.BLOCK_TERM_LIMIT = 4000
        self.stemmer = PorterStemmer()

        # Footer blacklist
        self.footer_blacklist = [
            "SenateResolution", "VPRGS-9",
            "Policy on Intellectual", "SpectrumLicence"
        ]

        # ensure folder exists
        if not os.path.exists("blocks"):
            os.makedirs("blocks")

        self.logger.info(f"Spider initialized with max_documents={self.max_documents}")

    # -----------------------------
    # CRAWLING LOGIC
    # -----------------------------

    # Spider initializes at main page
    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_main_page, dont_filter=True, priority=2000)

    # Spider crawls from main to document type page
    def parse_main_page(self, response):
        url_1 = response.xpath('//a[contains(text(), "by Document Type")]/@href').get()

        if url_1:
            url_2 = response.urljoin(url_1)
            yield Request(url=url_2, callback=self.parse_document_type_page, priority=2000)

    # Spider crawls from document type page to thesis page
    def parse_document_type_page(self, response):
        url_3 = response.xpath('//a[text()="Thesis"]/@href').get()

        if url_3:

            url_4 = response.urljoin(url_3)

            yield Request(url=url_4,callback=self.parse_thesis, dont_filter=True, priority=2000)

    # Spider crawls from thesis page to phd and masters page
    def parse_thesis(self, response):
        self.logger.info("Step 3: At Thesis Hub. Scheduling sequences...")

        # High Priority
        phd_url = response.xpath('//a[text()="PhD"]/@href').get()
        if phd_url:
            yield Request(url=response.urljoin(phd_url),callback=self.parse_thesis_list, priority=2000,dont_filter=True)

        # Lower Priority
        masters_url = response.xpath('//a[text()="Masters"]/@href').get()
        if masters_url:
            yield Request(url=response.urljoin(masters_url),callback=self.parse_thesis_list,priority=500,dont_filter=True)


    # Spider crawls to each year page for both phd and masters theses
    def parse_thesis_list(self, response):
        """
        Step 5: On the PhD Page.
        Selects ONLY the list of years (ignoring the toolbox menu).
        """
        self.logger.info(f"Step 5: Parsing Year URLs at {response.url}")

        # CSS Sibling Selector:
        # Finds the 'intro' text div, then selects the UL immediately following it.
        year_links = response.xpath(r'//a[re:test(text(), "^\d{4}$")]/@href').getall()

        for link in year_links:
            # 1. Validation (Skip empty or non-relative links)
            if not link or link.startswith(('javascript:', '#', 'mailto:')):
                continue

            # 2. Convert "2025.html" -> "https://.../2025.html"
            absolute_url = response.urljoin(link)

            self.logger.info(f"Queueing Year: {absolute_url}")

            # 3. Schedule the crawl for that specific year
            yield Request(
                url=absolute_url,
                callback=self.parse,  # Hand over to PDF Hunter
                priority=1000,
                dont_filter=False
            )


    # Main parse method - extracts PDFs and follows links (original spider implementation
    def parse(self, response):

        # If the response is not text stop immediately
        if not isinstance(response, TextResponse):
            self.logger.info(f"Skipping binary response (video/image): {response.url}")
            return

        # Stop if upperbound reached (if max_documents = None --> keep crawling until no more PDFs are found)
        if self.max_documents and self.document_count >= self.max_documents:
            self.logger.info(f"Limit reached. Stopping.")
            return


        #self.logger.info(f"Crawling: {response.url}")

        # Find all PDF links within each crawled page
        pdf_links = response.css('a[href*=".pdf"]::attr(href)').getall()

        for pdf_url in pdf_links:
            # Check limit before scheduling each PDF
            if self.max_documents and self.document_count >= self.max_documents:
                self.logger.info(f"Limit reached while scheduling PDFs. Stopping.")
                return

            full_pdf_url = response.urljoin(pdf_url)

            # Skip blacklisted PDFs
            if any(junk in full_pdf_url for junk in self.footer_blacklist):
                continue

            self.pdf_found += 1

            # # Extract title
            # title_element = response.xpath(f'//a[@href="{pdf_url}"]/text()').get()
            # if not title_element:
            #     title_element = response.xpath(f'//a[@href="{pdf_url}"]/..//text()').get()
            # title = title_element.strip() if title_element else "Unknown Title"

            # self.logger.info(f"Found PDF #{self.pdf_found}: {title}")

            # High priority for PDFs
            yield Request(
                full_pdf_url,
                callback=self.parse_pdf,
                meta={'url': response.url,'download_timeout': 300},
                priority=1000,
                dont_filter=True
            )

        # Follow internal links only if limit not reached (avoids unnecessary crawling)
        if not self.max_documents or self.document_count < self.max_documents:
            all_links = response.css('a::attr(href)').getall()

            for link in all_links:
                if not link or '.pdf' in link.lower():
                    continue
                if link.startswith(('mailto:', 'javascript:', '#')):
                    continue

                yield response.follow(link, callback=self.parse, priority=0)

    # -----------------------------
    # PDF PARSING
    # -----------------------------
    def parse_pdf(self, response):
        """Parse PDF and extract text"""

        # Check upperbound before processing PDF
        if self.max_documents and self.document_count >= self.max_documents:
            self.logger.info(f"Skipping PDF - limit already reached")
            return

        document_url = response.url
        # document_title = response.meta.get('title', 'Unknown Title')

        try:
            self.logger.info(f"Processing PDF")

            # Read PDF with PyPDF2
            pdf_file = io.BytesIO(response.body)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            # Extract text from all pages
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            extracted_text = " ".join(text_parts)

            # Check if we got meaningful text
            if not extracted_text or len(extracted_text.strip()) < 50:
                self.logger.warning(f"Could not extract meaningful text from PDF")
                return

            # Increment document count
            self.document_count += 1
            doc_id = self.document_count

            self.logger.info(f"Successfully processed PDF #{doc_id}")

            # Tokenize and add to SPIMI index
            tokens = self.tokenize(extracted_text)
            self.add_to_spimi_block(tokens, doc_id, document_url)

            # Check if we've reached the limit
            if self.max_documents and self.document_count >= self.max_documents:
                self.logger.critical(f"Reached limit of {self.max_documents} documents. Closing spider.")
                raise CloseSpider(reason=f'Reached max_documents limit: {self.max_documents}')  # Local throw within try block

        except CloseSpider:
            # Re-raise CloseSpider to scrapy scheduler to really close the spider
            raise
        except Exception as e:
            self.logger.error(f"Error processing PDF {document_url}: {e}")

    # -----------------------------
    # TOKENIZATION
    # -----------------------------
    # Reusing Project 1 tokenize
    def tokenize(self, text):
        import re
        text = text.lower()
        tokens = re.findall(r'\b[a-z]+\b', text)

        clean = []
        for t in tokens:
            if t in self.STOPWORDS:
                continue
            clean.append(self.stemmer.stem(t))
        return clean

    # -----------------------------
    # SPIMI ADD TO BLOCK
    # -----------------------------
    def add_to_spimi_block(self, tokens, doc_id,  url):
        term_freq = Counter(tokens)

        for term, freq in term_freq.items():
            if term not in self.inverted_block:
                self.inverted_block[term] = []

            self.inverted_block[term].append({
                "doc": doc_id,
                "freq": freq,
                "url": url
            })

        # Check if block is full
        if len(self.inverted_block) >= self.BLOCK_TERM_LIMIT:
            self.flush_block()

    # -----------------------------
    # FLUSH BLOCK TO DISK
    # -----------------------------
    def flush_block(self):
        self.block_number += 1
        block_file = f"blocks/block_{self.block_number}.json"

        self.logger.info(f"Flushing SPIMI block #{self.block_number} to disk ({len(self.inverted_block)} terms)")

        with open(block_file, "w") as f:
            json.dump(self.inverted_block, f)

        # Reset memory
        self.inverted_block = {}

    # -----------------------------
    # MERGE BLOCKS AT END TO FORM INDEX.JSON
    # -----------------------------
    def closed(self, reason):
        self.logger.info(f"Spider closing. Reason: {reason}")
        self.logger.info(f"Total documents processed: {self.document_count}")

        # Flush remaining block
        if len(self.inverted_block) > 0:
            self.flush_block()

        if self.block_number == 0:
            self.logger.warning("No blocks created - no documents were processed")
            return

        self.logger.info("Merging SPIMI blocks...")

        final_index = {}

        # Load and merge all blocks
        for i in range(1, self.block_number + 1):
            block_file = f"blocks/block_{i}.json"
            if not os.path.exists(block_file):
                self.logger.warning(f"Block file {block_file} not found")
                continue

            with open(block_file, "r") as f:
                block = json.load(f)

            for term, postings in block.items():
                if term not in final_index:
                    final_index[term] = []
                final_index[term].extend(postings)

        # Save final merged index
        with open("index.json", "w") as f:
            json.dump(final_index, f, indent=2)

        self.logger.info(f"Final index saved! {len(final_index)} terms indexed.")

    # -----------------------------
    # STOPWORDS
    # -----------------------------
    STOPWORDS = {
        "the", "and", "a", "an", "of", "to", "in", "on", "for", "is", "are",
        "with", "that", "this", "it", "as", "by", "be", "from", "at", "was",
        "were", "or", "but", "not", "can", "could", "should", "would", "may",
        "also", "we", "they", "their", "its", "these", "those", "such"
    }