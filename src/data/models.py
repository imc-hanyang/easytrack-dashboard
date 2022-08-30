from datetime import datetime as dt
from datetime import timedelta as td

# libs
from peewee import AutoField, TextField, ForeignKeyField, TimestampField
from peewee import Model, PostgresqlDatabase
from playhouse.postgres_ext import BinaryJSONField

# app
from dashboard.settings import DATABASES as DB

db = PostgresqlDatabase(
    database=DB["default"]["NAME"],
    host=DB["default"]["HOST"],
    port=DB["default"]["PORT"],
    user=DB["default"]["USER"],
    password=DB["default"]["PASSWORD"]
)


class User(Model):
    id = AutoField(primary_key=True)
    email = TextField(unique=True)
    name = TextField()
    session_key = TextField(default=None)
    tag = TextField(default=None)

    class Meta:
        database = db
        db_table = 'user'
        schema = 'easytrack'


class Campaign(Model):
    id = AutoField(primary_key=True)
    owner = ForeignKeyField(User, on_delete='CASCADE')
    name = TextField()
    start_ts = TimestampField(default=dt.now)
    end_ts = TimestampField(default=lambda: dt.now() + td(days=90))

    class Meta:
        database = db
        db_table = 'campaign'
        schema = 'easytrack'


class DataSource(Model):
    id = AutoField(primary_key=True)
    name = TextField(unique=True)
    icon_name = TextField()

    class Meta:
        database = db
        db_table = 'data_source'
        schema = 'easytrack'


class CampaignDataSources(Model):
    campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
    data_source = ForeignKeyField(DataSource, on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'campaign_data_source'
        schema = 'easytrack'
        indexes = (
            (('campaign', 'data_source'), True),  # unique together
        )


class Supervisor(Model):
    campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
    user = ForeignKeyField(User, on_delete='CASCADE')

    class Meta:
        database = db
        db_table = 'supervisor'
        schema = 'easytrack'
        indexes = (
            (('campaign', 'user'), True),  # unique together
        )


class Participant(Model):
    campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
    user = ForeignKeyField(User, on_delete='CASCADE')
    join_ts = TimestampField(default=dt.now)
    last_heartbeat_ts = TimestampField(default=dt.now)

    class Meta:
        database = db
        db_table = 'participant'
        schema = 'easytrack'

        indexes = (
            (('campaign', 'user'), True),  # unique together
        )


class HourlyStats(Model):
    participant = ForeignKeyField(Participant, on_delete='CASCADE')
    data_source = ForeignKeyField(DataSource, on_delete='CASCADE')
    ts = TimestampField()
    amounts = BinaryJSONField()

    class Meta:
        database = db
        db_table = 'hourly_stats'
        schema = 'easytrack'

        indexes = (
            (('participant', 'data_source'), False),  # selection by participant and/or data source
            (('ts',), False),  # selection by timestamp
        )


# connect and prepare tables
db.connect()
db.create_tables([
    User,
    Campaign,
    DataSource,
    CampaignDataSources,
    Supervisor,
    Participant,
    HourlyStats
])
