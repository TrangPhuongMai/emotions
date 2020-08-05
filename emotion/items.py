# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EmotionItem(scrapy.Item):
    img_url = scrapy.Field()
    img = scrapy.Field()
