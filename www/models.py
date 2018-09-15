import time 
from orm import Model, StringField, IntegerField, FloatField, TextField,  BooleanField


class User(Model):
    __table__ = 'users'

    id = IntegerField(primary_key=True)
    email = StringField(column_type='varchar(50)')
    password = StringField(column_type='varchar(50)')
    admin = BooleanField()
    name = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')
    created_at = FloatField(default=time.time)

class Bolg(Model):
    __table__ = 'blogs'

    id = IntegerField(primary_key=True)
    user_id = IntegerField()
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(500)')
    name = StringField(column_type='varchar(50)')
    summary = StringField(column_type='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)

class Comment(Model):
    __table__ = 'comments'

    id = IntegerField(primary_key=True)
    blog_id = IntegerField()
    user_id = IntegerField()
    user_name = StringField(column_type='varchar(50)')
    user_image = StringField(column_type='varchar(50)')
    content = TextField()
    created_at = FloatField(default=time.time)