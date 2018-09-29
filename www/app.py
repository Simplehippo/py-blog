import logging; logging.basicConfig(level=logging.INFO)
import asyncio, json, orm, os, time, hashlib
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from webs import add_routes, add_static
from config import configs
from models import User
from handlers import COOKIE_NAME, _COOKIE_KEY
from datetime import datetime

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
    filters = kw.get('filters', None)
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__jinja2_env__'] = env

def datetime_filter(t):
    delta = int(time.time() - t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt = datetime.fromtimestamp(t)
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day)

async def auth_middleware(app, handler):
    async def auth(request):
        logging.info('auth_middleware check user: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user = await cookie2user(cookie_str)
            if user:
                logging.info('set current user: %s' % user.email)
                request.__user__ = user
        if request.path.startswith('/manage/') and (request.__user__ is None or not request.__user__.admin):
            return web.HTTPFound('/signin')
        return await handler(request)
    return auth

async def cookie2user(cookie_str):
    if not cookie2user:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        id, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(id=int(id))
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.password = '******'
        return user
    except Exception as e:
        logging.info(e)
        return None

async def logger_middleware(app, handler):
    async def logger(request):
        logging.info('logging_middleware handler Request: %s %s' % (request.method, request.path))
        return (await handler(request))
    return logger

async def response_middleware(app, handler):
    async def response(request):
        logging.info('response_middleware handler...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
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
                r['__user__'] = request.__user__
                html = app['__jinja2_env__'].get_template(template).render(**r)
                resp = web.Response(body=html.encode('utf8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp 

        #default response 
        resp = web.Response(body=str('默认的返回内容, 检查response_middlewares是否出错(仅用于测试)').encode('utf8'))
        resp.content_type = 'text/plain;charset=utf-8'      
        return resp
    return response

async def init(loop):
    #初始化数据库连接池
    await orm.create_pool(loop, **configs['db'])
    #初始化aiohttp服务器
    app = web.Application(
        loop=loop,
        middlewares=[logger_middleware, auth_middleware, response_middleware]
    )
    #初始化模板引擎
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    #扫描handlers内的handler,并自动注册
    add_routes(app, 'handlers')
    #增加静态资源的访问
    add_static(app)
    server = await loop.create_server(app.make_handler(), configs['server']['ip'], 9000)
    logging.info('server started at http://%s:9000...' % configs['server']['ip'])
    return server

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()




