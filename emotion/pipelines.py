# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from scrapy.pipelines.images import ImagesPipeline
import os
import mimetypes
import time
import hashlib
from scrapy.utils.python import to_bytes
from scrapy.http.request import Request
from scrapy.pipelines.files import FSFilesStore, S3FilesStore, GCSFilesStore, FTPFilesStore, FilesPipeline
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/nero/emotions/image crawler-aba2ff8f069c.json"

class EmotionPipeline(ImagesPipeline):
    STORE_SCHEMES = {
        '': FSFilesStore,
        'file': FSFilesStore,
        's3': S3FilesStore,
        'gs': GCSFilesStore,
        'ftp': FTPFilesStore
    }

    def get_media_requests(self, item, info):
        for index, x in enumerate(item['image_urls']):
            try:
                yield Request(x, meta={'keyword': item['keyword'][-1], 'image_name': item['image_name'][index]})
            except:
                yield Request(x, meta={'keyword': item['keyword'][-1]})

    def file_path(self, request, response=None, info=None, *, item=None):

        try:
            image_guid = str(request.meta['image_name']).split('/')[-1].replace('.jpg', ' ')
        except Exception as e:
            image_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
        return '{file_name}/{image_guid}.jpg'.format(file_name=request.meta['keyword'], image_guid=image_guid, )

