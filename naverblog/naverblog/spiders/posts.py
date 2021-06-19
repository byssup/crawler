import re
import json
from datetime import datetime
from urllib import parse


import scrapy
import xmltodict
from bs4 import BeautifulSoup


class Spider(scrapy.Spider):

    name = 'posts'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(Spider, cls).from_crawler(crawler, *args, **kwargs)
        spider.pattern_body = re.compile(r'\s+')       
        return spider

    def start_requests(self):
        _id = 'yousy1009'
        url = 'http://rss.blog.naver.com/{}.xml'.format(_id)
        yield scrapy.Request(url)

    def parse(self, response):
        try:        
            od = xmltodict.parse(response.text)
            for ele in od['rss']['channel']['item']:
                write_time = datetime.strptime(ele['pubDate'], '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d %H:%M:%S')
                parsed = parse.urlparse(ele['link'])                
                _, blog_id, post_srl = tuple(parsed.path.split('/'))
                url = 'https://blog.naver.com/PostView.nhn?blogId={}&logNo={}'.format(blog_id, post_srl)
                meta = { 
                    'post':
                    {
                        'guid': ele['guid'],
                        'title': ele['title'],
                        'category': ele['category'],
                        'link': ele['link'],
                        'wrtieTime': write_time,               
                        'blog_id': blog_id,
                        'post_srl': post_srl
                    }
                }
                yield scrapy.Request(url, meta=meta, callback=self.parse_detail)
        except Exception as msg:
            print('msg : {}'.format(str(msg)))  

    def parse_detail(self, response):
        bs = BeautifulSoup(response.text, 'lxml', from_encoding=response.encoding)
        matched = bs.find_all('div', class_='se-component-content')
        texts = []
        for obj in matched:
            text = obj.get_text()
            text = re.sub(self.pattern_body, ' ', text).strip()
            if not text:
                continue
            texts.append(text)
        body = ' '.join(texts).strip().replace(u'\u200b', '')
        post_meta = response.meta['post']

        yield {
            '_id': 'naverblog_{}_{}'.format(post_meta['blog_id'], post_meta['post_srl']),
            **post_meta,
            'body': body,
            'crawled_at': datetime.now()
        }

