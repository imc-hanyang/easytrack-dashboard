from datetime import datetime as dt
from datetime import timedelta as td

# libs
from peewee import AutoField, TextField, ForeignKeyField, TimestampField
from peewee import Model, PostgresqlDatabase
from playhouse.postgres_ext import BinaryJSONField
import psycopg2.extras as pg2_extras
import psycopg2 as pg2

# app
from dashboard.settings import DATABASES as DB
from utils import failIfNone

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
		schema = 'et'


class Campaign(Model):
	id = AutoField(primary_key=True)
	owner = ForeignKeyField(User, on_delete='CASCADE')
	name = TextField()
	start_ts = TimestampField(default=dt.now)
	end_ts = TimestampField(default=lambda: dt.now() + td(days=90))

	class Meta:
		database = db
		db_table = 'campaign'
		schema = 'et'


class DataSource(Model):
	id = AutoField(primary_key=True)
	name = TextField(unique=True)
	icon_name = TextField()

	class Meta:
		database = db
		db_table = 'data_source'
		schema = 'et'


class CampaignDataSources(Model):
	campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
	data_source = ForeignKeyField(DataSource, on_delete='CASCADE')

	class Meta:
		database = db
		db_table = 'campaign_data_source'
		schema = 'et'
		indexes = (
			(('campaign', 'data_source'), True),  # unique together
		)


class Supervisor(Model):
	campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
	user = ForeignKeyField(User, on_delete='CASCADE')

	class Meta:
		database = db
		db_table = 'supervisor'
		schema = 'et'
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
		db_table = 'campaign_participant_stats'
		schema = 'et'


class HourlyStats(Model):
	campaign = ForeignKeyField(Campaign, on_delete='CASCADE')
	user = ForeignKeyField(User, on_delete='CASCADE')
	data_source = ForeignKeyField(DataSource, on_delete='CASCADE')
	amounts = BinaryJSONField()

	class Meta:
		database = db
		db_table = 'campaign_participant_stats'
		schema = 'et'


class DataTable:
	@staticmethod
	def __get_name(
		participant: Participant
	) -> str:
		"""
		Returns a table name for particular campaign participant
		:param participant: the participant that includes campaign and user id information
		:return: name of the corresponding data table
		"""
		failIfNone(participant)
		return '_'.join([
			f'campaign{participant.campaign.id}',
			f'user{participant.id}'
		])

	@staticmethod
	def create(
		participant: Participant
	) -> None:
		"""
		Creates a table for a participant to store their data
		:param participant: user participating in a campaign
		:return:
		"""
		con = pg2.connect(
			database=DB["default"]["NAME"],
			host=DB["default"]["HOST"],
			port=DB["default"]["PORT"],
			user=DB["default"]["USER"],
			password=DB["default"]["PASSWORD"]
		)
		table_name = DataTable.__get_name(
			participant=failIfNone(participant)
		)
		cur = con.cursor()

		cur.execute('create schema if not exists data')
		cur.execute(f'create table if not exists data.{table_name}(data_source_id int references et.data_source (id), ts timestamp, val jsonb)')
		cur.execute(f'create index if not exists idx_{table_name}_ts on data.{table_name} (ts)')
		con.commit()

		cur.close()
		con.close()

	@staticmethod
	def insert(
		participant: Participant
	) -> None:
		raise NotImplementedError('Implement this method!')  # todo impl

	@staticmethod
	def select(
		participant: Participant
	) -> pg2_extras.DictRow:
		raise NotImplementedError('Implement this method!')  # todo impl


# connect and prepare tables
db.connect()
db.create_tables([User, Campaign, DataSource, Supervisor, Participant, HourlyStats])
