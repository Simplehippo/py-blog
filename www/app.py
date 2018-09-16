import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, orm, os
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from webs import add_routes
from config import configs

def init_jinja2(app, **kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set jinja2 template path: %s' % path)
    env = Environment(loader=FileSystemLoader(path), **options)
    app['__jinja2_env__'] = env

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
                html = app['__jinja2_env__'].get_template(template).render(**r)
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
    await orm.create_pool(loop, 
        user=configs['db']['user'], 
        password=configs['db']['password'], 
        db=configs['db']['database']
    )
    #初始化aiohttp服务器
    app = web.Application(
        loop=loop,
        middlewares=[logger_middlewares, response_middlewares]
    )
    #初始化模板引擎
    init_jinja2(app)
    #扫描handlers内的handler,并自动注册
    add_routes(app, 'handlers')
    server = await loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return server

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()




