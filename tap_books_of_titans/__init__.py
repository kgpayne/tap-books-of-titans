#!/usr/bin/env python3
import os
import json
import logging

import singer
from singer import utils, metadata
from singer.catalog import Catalog, CatalogEntry
from singer.schema import Schema

from scrapy import signals
from scrapy.crawler import CrawlerProcess, Crawler
from scrapy.utils.project import get_project_settings

from .books_of_titans_scraper.spiders.books_of_titans_spider import (
    RecommendationsSpider
)


logging.getLogger('scrapy').propagate = False

REQUIRED_CONFIG_KEYS = []
LOGGER = singer.get_logger()
SCRAPY_SETTINGS = dict(
    BOT_NAME='books_of_titans_scraper',
    SPIDER_MODULES=['tap_books_of_titans.books_of_titans_scraper.spiders'],
    NEWSPIDER_MODULE='tap_books_of_titans.books_of_titans_scraper.spiders',
    ROBOTSTXT_OBEY=True,
    FEED_EXPORT_ENCODING='utf-8'
)


def get_abs_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), path)


def load_schemas():
    """ Load schemas from schemas folder """
    schemas = {}
    for filename in os.listdir(get_abs_path('schemas')):
        path = get_abs_path('schemas') + '/' + filename
        file_raw = filename.replace('.json', '')
        with open(path) as file:
            schemas[file_raw] = Schema.from_dict(json.load(file))
    return schemas


def discover():
    raw_schemas = load_schemas()
    streams = []
    for stream_id, schema in raw_schemas.items():
        # TODO: populate any metadata and stream's key properties here..
        stream_metadata = []
        key_properties = []
        streams.append(
            CatalogEntry(
                tap_stream_id=stream_id,
                stream=stream_id,
                schema=schema,
                key_properties=key_properties,
                metadata=stream_metadata,
                replication_key=None,
                is_view=None,
                database=None,
                table=None,
                row_count=None,
                stream_alias=None,
                replication_method=None,
            )
        )
    return Catalog(streams)


def run_crawler():
    crawled_items = []

    def add_item(item):
        crawled_items.append(item)

    process = CrawlerProcess(settings=SCRAPY_SETTINGS)
    crawler = Crawler(RecommendationsSpider)
    crawler.signals.connect(add_item, signals.item_scraped)
    process.crawl(crawler)
    process.start()

    return crawled_items


def sync(config, state, catalog):
    """ Sync data from tap source """
    # Loop over selected streams in catalog
    for stream in catalog.get_selected_streams(state):
        LOGGER.info("Syncing stream:" + stream.tap_stream_id)

        singer.write_schema(
            stream_name=stream.tap_stream_id,
            schema=stream.schema.to_dict(),
            key_properties=stream.key_properties,
        )

        if stream.tap_stream_id == 'recommendations':
            for row in run_crawler():
                singer.write_records(stream.tap_stream_id, [row])

    return


@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    # If discover flag was passed, run discovery mode and dump output to stdout
    if args.discover:
        catalog = discover()
        catalog.dump()
    # Otherwise run in sync mode
    else:
        if args.catalog:
            catalog = args.catalog
        else:
            catalog = discover()
        sync(args.config, args.state, catalog)


if __name__ == "__main__":
    main()
