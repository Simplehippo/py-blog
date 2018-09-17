#orm

__author__ = '杨育才' 
import logging; logging.basicConfig(level=logging.INFO)
import asyncio, aiomysql, time

#连接池
async def create_pool(loop, **kw):
    print('create databases connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host = kw.get('host', 'localhost'),
        port = kw.get('port', 3306),
        user = kw['user'],
        password = kw['password'],
        db = kw['database'],
        charset = kw.get('charset', 'utf8'),
        autocommit = kw.get('autocommit', True),
        maxsize = kw.get('maxsize', 10),
        minsize = kw.get('minsize', 1),
        loop = loop
    )

#select
async def select(sql, args=(), size=None):
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql.replace('?', '%s'), args)
            if size:
                rs = await cursor.fetchmany(size)
            else:
                rs = await cursor.fetchall()
    return rs

#execute     (insert, update, delete)
async def execute(sql, args, autocommit=True):
    global __pool
    async with __pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql.replace('?', '%s'), args)
                affectedrow = cursor.rowcount
                if not autocommit:
                    await conn.commit()
        except BaseException as e:
            if not autocommit:
                await conn.rollback()
            raise
    return affectedrow

def create_args_string(n):
    L = []
    for i in range(n):
        L.append('?')
    return ', '.join(L)

class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

class StringField(Field):
    def __init__(self, name=None, column_type='varchar(100)', primary_key=None, default=None):
        super().__init__(name, column_type, primary_key, default)

class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)

class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)

class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)

class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        #表名, 若声明了__table__属性,则是__table__内容,否则就是类名的小写
        table_name = attrs.get('__table__', None) or name.lower()
        mappings = dict()
        fields=[]
        primary_key=None
        for k,v in attrs.items():
            if isinstance(v, Field):
                #数据库字段名默认是类的属性名,这样可以缺省name属性了
                if not v.name:
                    v.name = k
                mappings[k] = v
                if v.primary_key:
                    if primary_key:
                        raise StandardError('Duplicate primary key for field: %s' % k)
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise StandardError('primary key is not found!')
        for k in mappings.keys():
            attrs.pop(k)
        table_primary_key = mappings.get(primary_key).name
        table_fields = list(map(lambda f:mappings.get(f).name, fields))        
        attrs['__table__'] = table_name
        attrs['__mappings__'] = mappings
        attrs['__fields__'] = fields
        attrs['__primary_key__'] = primary_key
        attrs['__table_fields__'] = table_fields
        attrs['__table_primary_key__'] = table_primary_key
        attrs['__select__'] = 'select %s, %s from %s' % (table_primary_key, ', '.join(table_fields), table_name) 
        attrs['__insert__'] = 'insert into %s(%s, %s) values(%s)' % (table_name, ', '.join(table_fields), table_primary_key, create_args_string(len(table_fields)+1))
        attrs['__update__'] = 'update %s set %s where %s=?' % (table_name, ', '.join(list(map(lambda f:'%s=?' % f, table_fields))), table_primary_key)
        attrs['__delete__'] = 'delete from %s where %s=?' % (table_name, table_primary_key)
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, values):
        self[key] = values

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if not value:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                setattr(self, key, value)
        return value
    
    def printAllInfo(self):
        for k, v in Student.__mappings__.items():
            print(k, v, self.getValueOrDefault(k))


    async def save(self):
        '(save) save obj to database'
        fields_values = list(map(self.getValueOrDefault, self.__fields__))
        fields_values.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, fields_values)
        if rows != 1:
            print('(save) failed insert , effected rows %s !' % rows)

    async def update(self):
        '(update) update obj to database'
        fields_values = list(map(self.getValueOrDefault, self.__fields__))
        fields_values.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__update__, fields_values)
        if rows != 1:
            print('(save) failed insert , effected rows %s !' % rows)

    async def remove(self):
        '(remove) remove obj from database'
        primary_key_values = self.getValueOrDefault(self.__primary_key__)
        rows = await execute(self.__delete__, primary_key_values)
        if rows != 1:
            print('(save) failed insert , effected rows %s !' % rows)        

    @classmethod
    async def find(cls, **kw):
        'find a row by some param'
        if len(kw) == 0:
            return None
        sql = '%s where ' % cls.__select__
        values = []
        for k, v in kw.items():
            sql += '%s = ? and ' % cls.__mappings__[k].name
            values.append(v)
        sql = sql[:-4]
        logging.info('(find) sql: %s' % sql)
        logging.info('(find) values: %s' % str(values))
        rs = await select(sql, values, 1)
        if len(rs) == 0:
            return None
        logging.info('(find) find success rs:%s' % rs)
        return cls(**rs[0])

