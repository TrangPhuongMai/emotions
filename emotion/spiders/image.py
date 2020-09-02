import scrapy
from scrapy.http import FormRequest, Request
import time
import re
import requests
from bs4 import BeautifulSoup
from scrapy_splash import SplashRequest
from emotion.items import EmotionItem
from scrapy.loader import ItemLoader
import time
import base64

def isnan_js(n): # recreate javascrpit isnan function since python dont have the equivalent
    bad_answer = True
    while bad_answer:
        try:
            num = int(n)
            return False
        except:
            return True


def adFly_decoder(url):
    left = []
    right = []
    for i in range(len(url)):
        if i % 2 == 0:
            right.append(url[i])
        else:
            left.append(url[i])

    url = right + left[::-1]
    m = 0
    while (m <= len(url)):
        if m == len(url):
            break
        if not isnan_js(url[m]):
            for R in range(m + 1, len(url)):
                if not isnan_js(url[R]):
                    S = int(url[m]) ^ int(url[R])
                    if (S < 10):
                        url[m] = S
                    m = R
                    break
        m = m + 1

    for i in range(len(url)):
        url[i] = str(url[i])
    url = base64.b64decode(''.join(url))
    url = str(url)
    return url[18:][:-17]


class ImageSpider(scrapy.Spider):
    name = 'image'
    urls = []
    start_urls = ['https://www.shutterstock.com/search/', ]

    def parse(self, response):
        # emotions = ['happy', 'neutral', 'displeasure', 'anger', 'rage']
        emotions = ['happy',]
        for emotion in emotions:
            yield Request(url=self.start_urls[0] + emotion + '?mreleased=true', callback=self.parse_stock, )

    def parse_stock(self, response):
        script = """
                function scroll_to(splash, x, y)
                    local js = string.format("window.scrollTo(%s, %s);",
                        tonumber(x),
                        tonumber(y))
                    return splash:runjs(js)
                end
                
                
                function get_doc_height(splash)
                    return splash:runjs([[
                    Math.max(
                        Math.max(document.body.scrollHeight, document.getElementById("content").scrollHeight),
                        Math.max(document.body.offsetHeight, document.getElementById("content").offsetHeight),
                        Math.max(document.body.clientHeight, document.getElementById("content").clientHeight)
                    )
                    )
                  ]])
                end
                
                function scroll_to_bottom(splash)
                    local y = get_doc_height(splash)
                    return scroll_to(splash, 0, y)
                end
                
                
                function main(splash)
                
                    local url = splash.args.url
                    assert(splash:go(url))
                    assert(splash:wait(0.5))
                    splash:stop()
                    
                    for i = 1, 10 do
                        scroll_to_bottom(splash)
                        assert(splash:wait(0.5))
                    end
                
                    splash:set_viewport_full()
                
                    return {
                        html = splash:html(),
                        png = splash:png { width = 640 },
                        har = splash:har(),
                    }
                end
        """
        yield SplashRequest(url=response.url, callback=self.parse_img, endpoint='execute',
                            args={'wait': 1, 'lua_source': script, 'url': response.url})
        # url = response.xpath('//a[contains(text(),"Next")]').attrib['href']
        # print("------------------------- {} -------------------------".format(url))
        # yield Request(url='https://www.shutterstock.com'+str(url),callback=self.parse_stock)

    def parse_img(self, response):
        script = """
                function main(splash,args)
                    splash:go(args.url)
                    -- splash:wait(1)
                    local button = splash:select('#taifile')
                    button:mouse_click()
                    splash:wait(10)
                    return {
                        html = splash:html(),
                    }
                end
                """
        links = response.xpath('//img[@src][@alt!=""]')
        for link in links:
            link = link.xpath('@src').get()
            img_id = str(link).split('.')[-2].split('-')[-1]
            url = 'https://png.is/find?id=' + img_id
            yield SplashRequest(url=url,
                                callback=self.parse_adfBypass,
                                endpoint='execute',
                                args={'wait': 1, 'lua_source': script, 'url': url}
                                )

    def parse_adfBypass(self, response):
        url = response.css('#taifile').xpath('@href').get()  # now the find link button have return a usable link
        r = requests.get(url=url)
        soup = BeautifulSoup(r.content)
        links = soup.find_all('script',attrs={'type':"text/javascript"})
        ysmm = str(links[2]).split("ysmm")[1].split("'")[1]
        print(adFly_decoder(ysmm))
        # yield Request(url=url,callback=self.parse_bypassAdf,meta={'url':url})
        # yield SplashRequest(url=url, callback=self.parse_bypassAdf,



