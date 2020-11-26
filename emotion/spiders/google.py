import scrapy
from scrapy_splash import SplashRequest
from haralyzer import HarParser, HarPage
import json
import pandas as pd
from emotion.items import EmotionItem
from scrapy.loader import ItemLoader


class GoogleSpider(scrapy.Spider):
    name = 'google'
    start_urls = [
        'https://google.com',
    ]

    custom_settings = {
        'IMAGES_STORE': '/home/nero/emotions/google',
    }

    keywords = pd.read_csv('f.csv', header=None)
    k = []
    for pd_index in range(keywords.shape[0]):
        keyword = keywords.iloc[pd_index].fillna('').str.cat(sep=' ')
        k.append(keyword)
    keywords = k

    def __init__(self, *args, **kwargs):
        super(GoogleSpider, self).__init__(*args, **kwargs)
        self.img = 'https://google.com/search?q={}&tbm=isch'

    def parse(self, response):
        script = '''
        function main(splash, args)
          assert(splash:go(args.url))
          assert(splash:wait(0.5))
          local scroll_to = splash:jsfunc("window.scrollTo")
          for i=1,2 do
            scroll_to(0,i*1000)
            if i > 7000 then
                splash:wait(1.1)
            else 
                splash:wait(0.2)
            end
          end
          splash:set_viewport_full()
          buttons = splash:select_all('#islrg > div.islrc > div > a.wXeWr.islib.nfEiy.mM5pbd')

          for i,button in ipairs(buttons) do
              button:mouse_click()
              splash:wait(0.12)
          end

          return {
            html = splash:html(),
            png = splash:png(),
            har = splash:har(),
          }
        end
        '''

        for keyword in self.keywords:
            # yield SplashRequest(url=self.img.format(keyword), callback=self.parse_png, endpoint='execute',
            #                     args={'lua_source': script, })
            yield SplashRequest(url='https://google.com/search?q={}&tbm=isch'.format(keyword), callback=self.parse_png,
                                endpoint='execute',
                                args={'lua_source': script, 'timeout': 36000, }, meta={'keyword': keyword})

    def parse_png(self, response):
        l = ItemLoader(EmotionItem(), response=response)
        har_parser = response.data['har']
        for i in range(len(har_parser['log']['entries'])):
            img_url = har_parser['log']['entries'][i]['request']['url']
            if 'jpg' in str(img_url):
                l.add_value('image_urls', img_url)
                l.add_value('keyword',response.meta['keyword'])
                yield l.load_item()
        # har_parser = HarParser(json.loads(har_parser))
        # print(har_parser)
