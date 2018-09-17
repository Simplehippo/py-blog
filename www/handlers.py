import logging; logging.basicConfig(level=logging.INFO)
from webs import get, post
from aiohttp import web
from models import Blog, User, Comment
import time

@get('/')
async def index(request):
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

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

@get('/api/users')
async def api_get_users(request):
    users = [
        User(id='1', name='yang', created_at=time.time()-120),
        User(id='2', name='yucai', created_at=time.time()-3600),
        User(id='3', name='learn python', created_at=time.time()-7200)
    ]
    return {
        'users':users
    }

