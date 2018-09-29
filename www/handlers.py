import logging; logging.basicConfig(level=logging.INFO)
from webs import get, post
from aiohttp import web
from models import Blog, User, Comment
import time, json, re
from apis import APIError, APIValueError, APIResourceNotFoundError, APIPermissionError, Page
from config import configs
import hashlib, markdown2

COOKIE_NAME = 'blog_user'
_COOKIE_KEY = configs['session']['secret']
_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.password, expires, _COOKIE_KEY)
    L = [str(user.id), expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

def check_admin(request):
    if request.__user__ is None or not request.__user__.admin:
        raise APIPermissionError()

def get_page_index(page_str):
    p = 1
    try:
        p = int(page_str)
    except ValueError as e:
        pass
    if p < 1:
        p = 1
    return p

def text2html(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

@get('/')
async def index(request):
    blogs = await Blog.findAll(orderBy='created_at desc')
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

@get('/signout')
async def api_signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

@get('/manage/blogs')
async def manage_blogs(*, page='1'):
    return {
        '__template__': 'manage_blogs.html',
        'page_index': get_page_index(page)
    }

@get('/manage/blogs/create')
async def manage_create_blog():
    return {
        '__template__': 'manage_blog_edit.html',
        'id': '',
        'action': '/api/blog/create'
    }

@get('/manage/blogs/edit')
async def manage_edit_blog(*, id):
    return {
        '__template__': 'manage_blog_edit.html',
        'id': id,
        'action': '/api/blog/%s/edit' % id
    }

@get('/api/blogs')
async def api_blogs(*, page='1'):
    page_index = get_page_index(page)
    num = await Blog.findNumber('count(id)')
    p = Page(num, page_index)
    if num == 0:
        return dict(page=p, blogs=())
    blogs = await Blog.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    return dict(page=p, blogs=blogs)

@get('/api/blog/{id}')
async def api_get_blog(*, id):
    blog = await Blog.find(id=id)
    return blog

@post('/api/blog/create')
async def api_create_blog(request, *, name, summary, content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog = Blog(
        user_id=request.__user__.id, 
        user_name=request.__user__.name, 
        user_image=request.__user__.image, 
        name=name.strip(), 
        summary=summary.strip(), 
        content=content.strip()
    )
    await blog.save()
    return blog

@post('/api/blog/{id}/edit')
async def api_update_blog(id, request, *, name, summary, content):
    check_admin(request)
    blog = await Blog.find(id=id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    blog.content = content.strip()
    await blog.update()
    return blog

@post('/api/blog/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id=id)
    await blog.remove()
    return dict(id=id)

@get('/blog/{id}')
async def get_blog(id):
    blog = await Blog.find(id=id)
    comments = await Comment.findAll(blog_id=id, orderBy='created_at desc')
    for c in comments:
        c.html_content = text2html(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'blog': blog,
        'comments': comments
    }