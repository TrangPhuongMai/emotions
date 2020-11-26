import scrapy
from scrapy.http import FormRequest, Request
import time
import re
import requests
from bs4 import BeautifulSoup
from scrapy_splash import SplashRequest, SplashFormRequest
from emotion.items import EmotionItem
from scrapy.loader import ItemLoader
import time
import base64
import json

wait_for_elements = '''
                function wait_for_element(splash, css, maxwait)
                    if maxwait == nil then
                      maxwait = 10
                    end
                    return splash:wait_for_resume(string.format([[
                    function main(splash) {{
                        var selector = '%s';
                        var maxwait = %s;
                        var end = Date.now() + maxwait*1000;
                        function check() {{
                        if(document.querySelector(selector)) {{
                          splash.resume('Element found');
                        }} else if(Date.now() >= end) {{
                          var err = 'Timeout waiting for element';
                          splash.error(err + " " + selector);
                        }} else {{
                          setTimeout(check, 200);
                        }}
                      }}
                      check();
                    }}
                    ]], {css}, {maxwait}))
                end
        '''


def isnan_js(n):  # recreate javascrpit isnan function since python dont have the equivalent
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
    custom_settings = {
        'IMAGES_STORE': '/home/nero/emotions/shutterstock',
    }

    def parse(self, response):
        # emotions = ['happy', 'neutral', 'displeasure', 'anger', 'rage']
        # emotions = ['lingonberry+jam+on+bread', ]
        keywords = ['lingonberry', ]
        for keyword in keywords:
            yield Request(url=self.start_urls[0] + keyword, callback=self.parse_stock, meta={'keyword': keyword})
            # yield Request(url=self.start_urls[0] + emotion + '?mreleased=true', callback=self.parse_stock, )

    def parse_stock(self, response):
        script = """
                function main(splash)
                
                    local url = splash.args.url
                    assert(splash:go(url))
                    assert(splash:wait(0.5))
                    splash:set_viewport_full()
                    return {
                        html = splash:html(),
                        png = splash:png(),
                        har = splash:har(),
                    }
                end
        """
        yield SplashRequest(url=response.url, callback=self.parse_page, endpoint='execute',
                            args={'wait': 1, 'lua_source': script, 'url': response.url},
                            meta={'keyword': response.meta['keyword'], 'url': response.url})
        # url = response.xpath('//a[contains(text(),"Next")]').attrib['href']
        # print("------------------------- {} -------------------------".format(url))
        # yield Request(url='https://www.shutterstock.com'+str(url),callback=self.parse_stock)

    def parse_page(self, response):
        script = """
                function main(splash)

                    local url = splash.args.url
                    assert(splash:go(url))
                    assert(splash:wait(0.5))
                    splash:set_viewport_full()
                    return {
                        html = splash:html(),
                        png = splash:png(),
                        har = splash:har(),
                    }
                end
                """
        page = response.xpath(
            '//input[@class="o_input_theme_input-element oc_Y_4ccd2 b_J_d43c3 oc_ag_97089 b_aE_bfe35 o_input_theme_filled oc_Y_05eb2"]/@max').extract_first()
        for i in range(1, int(page) + 1):
            url = response.meta['url'] + '?page={}'.format(i)
            yield SplashRequest(url=url, callback=self.parse_api, endpoint='execute',
                                args={'lua_source': script, }, meta={'keyword': response.meta['keyword']})

    def parse_api(self, response):
        data = json.loads(response.xpath(
            '//script[@data-react-helmet="true" and @type="application/ld+json"]//text()').extract_first())
        for img in data:
            link = img['url']
            img_id = str(link).split('.')[-2].split('-')[-1]
            name = str(link).split('image-photo/')[-1].replace('-' + img_id, '')
            data = {'id': img_id, 'site': 'st',
                    '_token': ' '}
            print('https://png.is/tool/wheredoigo?id={}&site=st&_token={}'.format(data['id'], data['_token']))
            yield Request(
                url='https://png.is/tool/wheredoigo?id={}&site=st&_token={}'.format(data['id'], data['_token']),
                cookies=data, callback=self.parse_png, meta={'keyword': response.meta['keyword'], 'name': name})

    def parse_png(self, response):
        script = '''
    function main(splash, args)
        splash.private_mode_enabled = false
        splash:set_user_agent('Mozilla/5.0 (Linux; U; Android 4.4.2; en-us; SCH-I535 Build/KOT49H)')
        assert(splash:go(args.url))
        local button = splash:select('#findstock')
        button:mouse_click()
        ------------------------------
        splash:wait(7)
        ------------------------------
        splash:set_viewport_full()
        return {
            html = splash:html(),
            png = splash:png(),
            har = splash:har(),
        }
    end


        '''

        url = 'https://png.is/' + json.loads(response.xpath('//text()').get())['url']
        yield SplashRequest(url=url,
                            callback=self.parse_adfBypass,
                            endpoint='execute',
                            args={'lua_source': script, 'url': url},
                            meta={'keyword': response.meta['keyword'], 'name': response.meta['name']}
                            )

    def parse_adfBypass(self, response):
        url = response.css('#findstock').xpath('@href').get()  # now the find link button have return a usable link
        r = requests.get(url=url)
        soup = BeautifulSoup(r.content)
        links = soup.find_all('script', attrs={'type': "text/javascript"})
        ysmm = str(links[2]).split("ysmm")[1].split("'")[1]

        url = adFly_decoder(ysmm)
        yield Request(url=url, callback=self.parse_img,
                      meta={'keyword': response.meta['keyword'], 'name': response.meta['name'], 'url': url})
        # yield SplashRequest(url=url, callback=self.parse_bypassAdf,

    def parse_img(self, response):
        l = ItemLoader(item=EmotionItem(), response=response)
        img_url = response.css('body > div.container > div.row > div.col-md-12.abc.text-center > a').attrib['href']
        img_url = 'https://dl2.findandfound.ga' + img_url
        # 'https://dl2.findandfound.ga/image/bCKYKhQnwNDvHplGuI%2FEeFGbEg3d56ikTpBRaVBqAyhJ3BgPJj1jAGRZfM43B6WAXPMWDA1nvD22w1IwcE1Bvs9slXVtYsqtSOHEU9speA%2Fb1gRizyhnVjm8lCMplvdPXSeByY2AqFTbZY2QveCZ%2FjYUz%2BOjmUBfwEgDQqBp08xhHdTI8W5X7vTHnutD4Y5FejowsYM3l%2BWfhu5WBjE%2BQv5FBVcN7NPEPwyfCW0sKe15wknMTcUf68cjLoW2Rare--nh.jpg'
        print(response.meta['name'])
        print('hadsfkjasdhjfasdhkjfasdhkjfhsadjkfhasdkfhkjdhskjafahsdkjfhasdkjfhasdkjfhk')
        l.add_value('image_urls', img_url)
        l.add_value('image_name', response.meta['name'])
        l.add_value('keyword', response.meta['keyword'])
        yield l.load_item()
