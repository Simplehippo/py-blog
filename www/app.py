import logging; logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from aiohttp import web
from datetime import datetime

async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    server = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    print('Server listening http://127.0.0.1:9000')
    logging.info('server started at http://127.0.0.1:9000...')
    return server


async def index(req):
    print('$$$$$ router in index method...')
    return web.Response(body=b'<h1>web index</h1>', content_type='text/html')


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()




