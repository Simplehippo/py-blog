import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, orm
from aiohttp import web
from webs import add_routes
from config import configs

async def logger_middlewares(app, handler):
    async def logger(request):
        logging.info('logging_middlewares handler Request: %s %s' % (request.method, request.path))
        return (await handler(request))
    return logger

async def response_middlewares(app, handler):
    async def response(request):
        logging.info('response_middlewares handler...')
        r = await handler(request)
        if isinstance(r, web.Response):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):
            template = r.get('__template__', None)
            if template is None:
                #说明是json
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda obj: obj.__dict__).encode('utf8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                html = '<h1>模板引擎拿到的html....</h1>'
                resp = web.Response(body=html.encode('utf8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp 

        #default response 
        resp = web.Response(body=str(r).encode('utf8'))
        resp.content_type = 'text/plain;charset=utf-8'      
        return resp
    return response

async def init(loop):
    #初始化数据库连接池
    await orm.create_pool(loop, user=configs['db']['user'], password=configs['db']['password'], db=configs['db']['database'])
    #初始化aiohttp服务器
    app = web.Application(
        loop=loop,
        middlewares=[logger_middlewares, response_middlewares]
    )
    #扫描handlers内的handler,并自动注册
    add_routes(app, 'handlers')
    server = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return server

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()




