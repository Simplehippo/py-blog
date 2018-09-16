import logging; logging.basicConfig(level=logging.INFO)
import functools, asyncio, inspect, aiohttp

#GET请求的装饰器
def get(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

#POST请求的装饰器
def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator

class RequestHandler(object):
    def __init__(self, fn):
        self._func = fn
    
    async def __call__(self, request):
        #kw = ...
        
        return await self._func(request)

def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path =  getattr(fn, '__route__', None)
    if method is None or path is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    app.router.add_route(method, path, RequestHandler(fn))
    logging.info('server add_route(method:%s path:%s handlerName:%s)' % (method, path, fn.__name__))

def add_routes(app, module_name):
    n = module_name.rfind('.')
    if n == -1:
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[n+1:]
        print('name:', name)
        mod = getattr(__import__(module_name[:n], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)