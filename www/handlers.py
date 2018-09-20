import logging; logging.basicConfig(level=logging.INFO)
from webs import get, post
from aiohttp import web
from models import Blog, User, Comment
import time, json, re
from apis_error import APIError, APIValueError, APIResourceNotFoundError
from config import configs
import hashlib

COOKIE_NAME = 'yyc_user'
_COOKIE_KEY = configs['session']['secret']
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@get('/')
async def index(request):
    blogs = [
        Blog(id='1', name='Test Blog', created_at=time.time()-120),
        Blog(id='2', name='Something New', created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get('/register')
async def register(request):
    return {
        '__template__': 'register.html',
    }

@get('/signin')
async def signin(request):
    return {
        '__template__': 'signin.html',
    }

@post('/api/register')
async def api_register(*, email, name, password):
    print('api_register#####', name, email, password)
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_SHA1.match(password): 
        raise APIValueError('password')
    u = await User.find(email=email)
    if u is not None and len(u) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    user = User(email=email, password=password, name=name, image='blank')
    await user.save()
    user = await User.find(email=email)
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/api/signin')
async def api_signin(*, email, password):
    print('api_signin#####', email, password)
    if not email:
        raise APIValueError('email')
    if not password:
        raise APIValueError('password')
    user = await User.find(email=email)
    if user is None:
        raise APIError('signin:failed', 'email', 'Email is not register.')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.password = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [str(user.id), expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


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

