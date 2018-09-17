#用于简单的即时测试,为了快速看到编写,或修改的代码的效果

__author__ = '杨育才'

from models import User
from config import configs
import asyncio 
import orm

async def test():
    #初始化数据库连接池
    await orm.create_pool(loop, **configs['db'])
    #user = User(email='yang@qq.com', password='123456', name='yang', image='blank')
    #await user.save()
    u = await User.find(id=1002)
    print('u: ', u)
    #await u.remove()

loop = asyncio.get_event_loop()
loop.run_until_complete(test())
loop.run_forever()