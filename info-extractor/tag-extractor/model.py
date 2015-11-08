import json
import peewee
from peewee import *

config = json.loads(open('config.json').read())
db = MySQLDatabase(config.get('schema'), user=config.get('user'), passwd=config.get('password'))


class Tag(peewee.Model):
    name = peewee.CharField(primary_key=True)

    class Meta:
        database = db
