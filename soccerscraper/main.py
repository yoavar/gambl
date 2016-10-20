__author__ = 'yoav'

from scrapy import cmdline
cmdline.execute("scrapy crawl match_spider  -a min_page=1080550 -a max_page=1080552".split())