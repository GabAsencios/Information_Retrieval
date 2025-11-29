import scrapy
import json
import os
from scrapy.http import Request, TextResponse
from nltk.stem import PorterStemmer
from collections import Counter
from scrapy.exceptions import CloseSpider
import re
import fitz #PyMuPDF

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

        # Blacklisted from URL parsing
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

        self.logger.info(f"Parsing Year URLs at {response.url}")


        # Finds the div containing the list of years theses
        year_links = response.xpath(r'//a[re:test(text(), "^\d{4}$")]/@href').getall()

        for link in year_links:
            # Skip empty or non-relative links
            if not link or link.startswith(('javascript:', '#', 'mailto:')):
                continue

            # Convert to absolute URL
            absolute_url = response.urljoin(link)

            self.logger.info(f"Queueing Year: {absolute_url}")

            # Schedule the crawl for those specific year
            yield Request(
                url=absolute_url,
                callback=self.parse_doc,
                priority=1000,
                dont_filter=False
            )

        # # ---------------------
        # # MAIN PARSE FUNCTION (ORIGINAL ENTIRE DOMAIN CRAWLER)
        # # ---------------------
        # def parse_doc(self, response):
        #     """
        #     Parses the list of theses (Year page) and navigates to individual thesis pages.
        #     """
        #     # Safety check: Text only
        #     if not isinstance(response, TextResponse):
        #         return
        #
        #     # Check limit
        #     if self.max_documents and self.document_count >= self.max_documents:
        #         return
        #
        #
        #     # Finds all links like ".../id/eprint/12345/" inside the main content box
        #     thesis_links = response.css('div.ep_tm_main a[href*="/id/eprint/"]::attr(href)').getall()
        #
        #     for link in thesis_links:
        #         # Check limit before scheduling
        #         if self.max_documents and self.document_count >= self.max_documents:
        #             return
        #
        #         # Follow the link to the Thesis Page (Step 2)
        #         yield response.follow(
        #             link,
        #             callback=self.parse_thesis_page,
        #             priority=1000
        #         )


        # -------------------------
        # PARSE YEARS LIST PAGE
        # -------------------------
        # Scrapy Queues each year page for parsing
    def parse_doc(self, response):
        if not isinstance(response, TextResponse):
            return

        if self.max_documents and self.document_count >= self.max_documents:
            return

        # Extract only the main content box
        content_box = response.css('div.ep_tm_main')

        # Find links to thesis pages in content box
        thesis_links = content_box.css('a[href*="/id/eprint/"]::attr(href)').getall()

        for link in thesis_links:
            if self.max_documents and self.document_count >= self.max_documents:
                return

            yield response.follow(
                link,
                callback=self.parse_thesis_page,
                priority=1000
            )

    # ---------------------------------------------------------
    # PARSE THESIS PAGE FOR PDF URL
    # ---------------------------------------------------------
    # Queue thesis pages to be crawled into to later call for parse_pdf
    def parse_thesis_page(self, response):
        if self.max_documents and self.document_count >= self.max_documents:
            return

        # Find the .pdf link
        pdf_url = response.css('a[href*=".pdf"]::attr(href)').get()

        if pdf_url:
            full_pdf_url = response.urljoin(pdf_url)

            if any(junk in full_pdf_url for junk in self.footer_blacklist):
                return

            self.pdf_found += 1
            self.logger.info(f"Found PDF #{self.pdf_found} at {response.url}")

            yield Request(
                full_pdf_url,
                callback=self.parse_pdf,  # Calls PDF processing function
                meta={'url': response.url, 'download_timeout': 300},
                priority=2000,
                dont_filter=True
            )
        else:
            self.logger.warning(f"No PDF found on thesis page: {response.url}")

    # -------------------------
    # PDF PROCESSING FUNCTION
    # -------------------------
    def parse_pdf(self, response):
        """
        1. Open PDF
        2. Extract text
        3. Tokenize and add to SPIMI index
        """

        # Check upperbound before processing PDF
        if self.max_documents and self.document_count >= self.max_documents:
            self.logger.info(f"Skipping PDF - limit already reached")
            return

        document_url = response.url
        # document_title = response.meta.get('title', 'Unknown Title')

        try:
            self.logger.info(f"Processing PDF")

            # Read PDF with PyMuPDF
            with fitz.open(stream=response.body, filetype="pdf") as doc:
                text_parts = []
                for page in doc:
                    # Extract text from page
                    text_parts.append(page.get_text())

            extracted_text = " ".join(text_parts)

            # Check if we got meaningful text
            if not extracted_text or len(extracted_text.strip()) < 50:
                self.logger.warning(f"Could not extract meaningful text from PDF")
                return

            # Increment document count
            self.document_count += 1
            doc_id = self.document_count

            self.logger.info(f"Successfully processed PDF #{doc_id}, URL: {document_url}")

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
    # COMPRESSION & INDEX Helpers
    # -----------------------------

    def tokenize(self, text):
        """
        Tokenization pipeline:
        1. Case folding
        2. Split on non-alphanumeric (keep letters+numbers)
        3. Remove pure numeric terms
        4. Remove 30 stopwords
        5. Porter Stemming
        """
        # Case folding
        text = text.lower()

        # Split on any character that is NOT alphanumeric
        raw_tokens = re.split(r"[^a-z0-9]+", text)

        clean_tokens = []
        for t in raw_tokens:
            # Skip empty strings
            if not t:
                continue

            # Remove pure numeric terms
            if re.fullmatch(r'\d+', t):
                continue

            # Remove Stopwords
            if t in self.STOPWORDS:
                continue

            # Apply Stemming
            stemmed_t = self.stemmer.stem(t)
            clean_tokens.append(stemmed_t)

        return clean_tokens


    # SPIMI ADD TO BLOCK
    def add_to_spimi_block(self, tokens, doc_id, url):
        # Count frequency of each term in each document
        term_freq = Counter(tokens)

        for term, freq in term_freq.items():
            if term not in self.inverted_block:
                self.inverted_block[term] = []

            # Index format
            self.inverted_block[term].append({"docID": doc_id,  "freq": freq, "url": url})

        # Check if block is full, if full call flush_block()
        if len(self.inverted_block) >= self.BLOCK_TERM_LIMIT:
            self.flush_block()


    # FLUSH BLOCK TO DISK
    def flush_block(self):
        self.block_number += 1
        block_file = f"blocks/block_{self.block_number}.json"

        self.logger.info(f"Flushing SPIMI block #{self.block_number} to disk ({len(self.inverted_block)} terms)")

        with open(block_file, "w") as f:
            json.dump(self.inverted_block, f)

        # Reset memory for next block building
        self.inverted_block = {}


    # MERGE BLOCKS AT END TO FORM INDEX.JSON
    def closed(self, reason):
        self.logger.info(f"Spider closing.")
        self.logger.info(f"Total documents processed: {self.document_count}")

        # Flush remaining block
        if len(self.inverted_block) > 0:
            self.flush_block()

        if self.block_number == 0:
            self.logger.warning("No blocks created - increase max_documents")
            return

        self.logger.info("Merging SPIMI blocks...")

        final_index = {}

        # Load all blocks
        for i in range(1, self.block_number + 1):
            block_file = f"blocks/block_{i}.json"
            if not os.path.exists(block_file):
                self.logger.warning(f"Block file {block_file} not found")
                continue

            with open(block_file, "r") as f:
                block = json.load(f)
            # Merge block into final index
            for term, postings in block.items():
                if term not in final_index:
                    final_index[term] = []
                final_index[term].extend(postings)

        # Save final index
        with open("index.json", "w") as f:
            json.dump(final_index, f, indent=4)

        self.logger.info(f"Final index saved! {len(final_index)} terms indexed.")


    # 30 STOPWORDS
    STOPWORDS = {
        "the", "and", "a", "an", "of", "to", "in", "on", "for", "is", "are",
        "with", "that", "this", "it", "as", "by", "be", "from", "at", "was",
        "were", "or", "but", "not", "can", "could", "should", "would", "may",
        "also", "we", "they", "their", "its", "these", "those", "such"
    }