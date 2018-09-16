import logging; logging.basicConfig(level=logging.INFO)
from webs import get, post
from aiohttp import web

@get('/')
async def index(request):
    logging.info('$$$$$ router in index method...')
    return '<h1>hello index!!!!</h1>'


@get('/hello')
async def hello(request):
    logging.info('$$$$$ router in hello method...')
    return web.Response(body=b'<h1>hello</h1>', content_type='text/html')


@get('/jinja2')
async def jinja2(request):
    logging.info('$$$$$ router in jinja2 method...')
    return {
        '__template__':'test.html',
        'users':[{
            'name':'yang',
            'email':'yang@qq.com'
        },
        {
            'name':'cai',
            'email':'hhha@qq.com'
        }
        ]
    }