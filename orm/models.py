from datetime import datetime as dt
from datetime import timedelta as td
from typing import Dict, List, Optional

# libs
from peewee import AutoField, TextField, ForeignKeyField, TimestampField
from peewee import Model, PostgresqlDatabase
from playhouse.postgres_ext import BinaryJSONField
import psycopg2.extras as pg2_extras
import psycopg2 as pg2

# app
from dashboard.settings import DATABASES as DB
from orm.selectors import find_data_source
from utils import notnull, get_temp_filepath

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


class DataRecord:
	def __init__(
		self,
		data_source: DataSource,
		ts: dt,
		val: Dict
	):
		self.data_source = notnull(data_source)
		self.ts = notnull(ts)
		self.val = notnull(val)


class DataTable:
	con = None

	@staticmethod
	def __connect():
		if DataTable.con: return
		DataTable.con = pg2.connect(
			database=DB["default"]["NAME"],
			host=DB["default"]["HOST"],
			port=DB["default"]["PORT"],
			user=DB["default"]["USER"],
			password=DB["default"]["PASSWORD"]
		)

	@staticmethod
	def __get_name(
		participant: Participant
	) -> str:
		"""
		Returns a table name for particular campaign participant
		:param participant: the participant that includes campaign and user id information
		:return: name of the corresponding data table
		"""

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

		table_name = DataTable.__get_name(participant=participant)

		DataTable.__connect()
		cur = DataTable.con.cursor()
		cur.execute('create schema if not exists data')
		cur.execute(f'create table if not exists data.{table_name}(data_source_id int references et.data_source (id), ts timestamp, val jsonb)')
		cur.execute(f'create index if not exists idx_{table_name}_ts on data.{table_name} (ts)')
		cur.close()
		DataTable.con.commit()

	@staticmethod
	def insert(
		participant: Participant,
		data_source: DataSource,
		ts: dt,
		val: Dict
	) -> None:
		"""
		Creates a data record in raw data table (e.g. sensor reading)
		:param participant: participant of a campaign
		:param data_source: data source of the data record
		:param ts: timestamp
		:param val: value
		:return: None
		"""

		table_name = DataTable.__get_name(participant=participant)

		DataTable.__connect()
		cur = DataTable.con.cursor()
		cur.execute(f'insert into data.{table_name}(data_source_id, ts, val) values (%s,%s,%s)', (data_source, ts, pg2_extras.Json(val)))
		cur.close()
		DataTable.con.commit()

	@staticmethod
	def select_next_k(
		participant: Participant,
		data_source: DataSource,
		from_ts: dt,
		limit: int
	) -> List[DataRecord]:
		"""
		Retrieves next k data records from database
		:param participant: participant that has refernece to user and campaign
		:param data_source: type of data to retrieve
		:param from_ts: starting timestamp
		:param limit: max amount of records to query
		:return: list of data records
		"""

		table_name = DataTable.__get_name(participant=participant)

		DataTable.__connect()
		cur: pg2_extras.DictCursor = DataTable.con.cursor(cursor_factory=pg2_extras.DictRow)
		cur.execute(f'select data_source_id, ts, val from data.{table_name} where data_source_id = %s and ts >= %s limit %s', (data_source, from_ts, limit))
		rows = cur.fetchall()
		cur.close()

		return list(map(lambda row: DataRecord(
			data_source=find_data_source(data_source_id=row.data_source_id),
			ts=row.ts,
			val=row.val
		), rows))

	@staticmethod
	def select_range(
		participant: Participant,
		data_source: DataSource,
		from_ts: dt,
		till_ts: dt
	) -> List[DataRecord]:
		"""
		Retrieves filtered data based on provided range (start and end timestamps)
		:param participant: participant that has refernece to user and campaign
		:param data_source: type of data to retrieve
		:param from_ts: starting timestamp
		:param till_ts: ending timestamp
		:return: list of data records
		"""

		table_name = DataTable.__get_name(participant=participant)

		DataTable.__connect()
		cur: pg2_extras.DictCursor = DataTable.con.cursor(cursor_factory=pg2_extras.DictRow)
		cur.execute(f'select data_source_id, ts, val from data.{table_name} where data_source_id = %s and ts >= %s and ts < %s', (data_source, from_ts, till_ts))
		rows = cur.fetchall()
		cur.close()

		return list(map(lambda row: DataRecord(
			data_source=find_data_source(data_source_id=row.data_source_id),
			ts=row.ts,
			val=row.val
		), rows))

	@staticmethod
	def dump_to_file(
		participant: Participant,
		data_source: Optional[DataSource]
	) -> str:
		"""
		Dumps content of a particular DataTable into a downloadable file
		:param participant: participant that has reference to user and campaign
		:param data_source: which data source to dump
		:return: path to the downloadable file
		"""

		table_name = DataTable.__get_name(participant=participant)
		res = get_temp_filepath(filename=f'{table_name}.csv')

		DataTable.__connect()
		cur: pg2_extras.DictCursor = DataTable.con.cursor(cursor_factory=pg2_extras.DictRow)
		if data_source is None:
			cur.copy_to(file=res, table=table_name, sep=',')
		else:
			cur.copy_expert(
				sql=f"copy {table_name} to {res} with (format csv, delimiter ',', quote '\"')",
				file=res
			)
		cur.close()

		return res


# connect and prepare tables
db.connect()
db.create_tables([User, Campaign, DataSource, Supervisor, Participant, HourlyStats])
