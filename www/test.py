import asyncio, orm
from models import User

async def test(loop):
    await orm.create_pool(loop, user='root',password='123456', db='py_blog')
    user = User(name='Test', email='test1@example.com', password='1234567890', image='about:blank')
    await user.save()

loop = asyncio.get_event_loop()
tasks = [test(loop)]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()