from webs import get, post
from aiohttp import web

@get('/')
async def index(request):
    print('$$$$$ router in index method...')
    return '<h1>hello index!!!!</h1>'


@get('/hello')
async def hello(request):
    print('$$$$$ router in hello method...')
    return web.Response(body=b'<h1>hello</h1>', content_type='text/html')


@get('/jinja2')
async def jinja2(request):
    print('$$$$$ router in hello method...')
    return {
        '__template__':'hello',
        'params':'params'
    }