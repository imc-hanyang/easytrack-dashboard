from subprocess import PIPE
from tools import settings
from tools import utils
import subprocess
import json


# region 4. data management
def store_data_record(db_user, db_campaign, db_data_source, timestamp, value):
	session = get_db_connection()
	session.execute(f'insert into "data"."cmp{db_campaign.id}_usr{db_user.id}"("dataSourceId", "timestamp", "value") values (%s,%s,%s);', (
		db_data_source.id,
		timestamp,
		value
	))


def store_data_records(db_user, db_campaign, timestamp_list, data_source_id_list, value_list):
	data_sources: dict = {}
	for timestamp, data_source_id, value in zip(timestamp_list, data_source_id_list, value_list):
		if data_source_id not in data_sources:
			db_data_source = get_data_source(data_source_id=data_source_id)
			if db_data_source is None:
				continue
			data_sources[data_source_id] = db_data_source
		if data_sources[data_source_id] is not None:
			store_data_record(
				db_user=db_user,
				db_campaign=db_campaign,
				db_data_source=data_sources[data_source_id],
				timestamp=timestamp,
				value=value
			)


def get_next_k_data_records(db_user, db_campaign, from_timestamp, db_data_source, k):
	session = get_db_connection()
	k_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "timestamp">=%s and "dataSourceId"=%s order by "timestamp" asc limit {k} allow filtering;', (
		from_timestamp,
		db_data_source.id
	)).all()
	return k_records


def get_filtered_data_records(db_user, db_campaign, db_data_source, from_timestamp=None, till_timestamp=None):
	session = get_db_connection()
	if None not in [till_timestamp]:
		data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s order by "timestamp" allow filtering;', (
			db_data_source.id,
			from_timestamp,
			till_timestamp
		)).all()
	elif from_timestamp is not None:
		data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s order by "timestamp" allow filtering;', (
			db_data_source.id,
			from_timestamp
		)).all()
	elif till_timestamp is not None:
		data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp"<%s order by "timestamp" allow filtering;', (
			db_data_source.id,
			till_timestamp
		)).all()
	else:
		data_records = session.execute(f'select * from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s order by "timestamp" allow filtering;', (db_data_source.id,)).all()
	return data_records


def dump_data(db_campaign, db_user, db_data_source=None):
	file_path = utils.get_download_file_path(f'cmp{db_campaign.id}_usr{db_user.id}.bin.csv')
	# session.execute(f'copy "data"."cmp{db_campaign.id}_usr{db_user.id}" to %s with header = true;', (file_path,))
	if db_data_source:
		subprocess.run([settings.cqlsh_path, '-e', f"copy data.cmp{db_campaign.id}_usr{db_user.id} to \'{file_path}\' with header = true;"], stdout=PIPE, stderr=PIPE, shell=True)
	else:
		subprocess.run([settings.cqlsh_path, '-e', f"copy data.cmp{db_campaign.id}_usr{db_user.id} to \'{file_path}\' with header = true;"], stdout=PIPE, stderr=PIPE, shell=True)
	# subprocess.run([settings.cqlsh_path, '-e', f"copy data.cmp{db_campaign.id}_usr{db_user.id} to \'{file_path}\' with header = true;"], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
	# os.system(f'{settings.cqlsh_path} 127.0.0.1 -e "copy data.cmp{db_campaign.id}_usr{db_user.id} to \'{file_path}\' with HEADER = true"')
	return file_path


# endregion


# region 6. statistics
def get_participant_join_timestamp(db_user, db_campaign):
	session = get_db_connection()
	res = session.execute('select "joinTimestamp" from "stats"."campaignParticipantStats" where "userId"=%s and "campaignId"=%s allow filtering;', (
		db_user.id,
		db_campaign.id
	)).one()
	return None if res is None else res.joinTimestamp


def get_participant_last_sync_timestamp(db_user, db_campaign):
	session = get_db_connection()
	res = session.execute('select max("syncTimestamp") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s allow filtering;', (
		db_campaign.id,
		db_user.id,
	)).one()[0]
	return 0 if res is None else res


def get_participant_heartbeat_timestamp(db_user, db_campaign):
	session = get_db_connection()
	res = session.execute('select "lastHeartbeatTimestamp" from "stats"."campaignParticipantStats" where "userId" = %s and "campaignId" = %s allow filtering;', (
		db_user.id,
		db_campaign.id
	)).one()
	return 0 if res is None else res.lastHeartbeatTimestamp


def get_participants_amount_of_data(db_user, db_campaign):
	cur = get_db_connection()
	amount_of_samples = cur.execute(f'select sum("amountOfSamples") from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s allow filtering;', (
		db_campaign.id,
		db_user.id,
	)).one()[0]
	return 0 if amount_of_samples is None else amount_of_samples


def get_participants_per_data_source_stats(db_user, db_campaign):
	cur = get_db_connection()
	db_data_sources = get_campaign_data_sources(db_campaign=db_campaign)
	res_stats = []
	for db_data_source in db_data_sources:
		res = cur.execute(f'select "amountOfSamples" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
			db_campaign.id,
			db_user.id,
			db_data_source.id,
		)).one()
		amount_of_samples = 0 if res is None or res.amountOfSamples is None else res.amountOfSamples
		res = cur.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
			db_campaign.id,
			db_user.id,
			db_data_source.id,
		)).one()
		sync_timestamp = 0 if res is None or res.syncTimestamp is None else res.syncTimestamp
		res_stats += [(
			db_data_source,
			amount_of_samples,
			sync_timestamp
		)]
	return res_stats


def update_user_heartbeat_timestamp(db_user, db_campaign):
	session = get_db_connection()
	session.execute('update "stats"."campaignParticipantStats" set "lastHeartbeatTimestamp" = %s where "userId" = %s and "campaignId" = %s;', (
		utils.get_timestamp_ms(),
		db_user.id,
		db_campaign.id
	))


def remove_participant_from_campaign(db_user, db_campaign):
	session = get_db_connection()
	session.execute('delete from "stats"."campaignParticipantStats" where "userId" = %s and "campaignId" = %s;', (
		db_user.id,
		db_campaign.id
	))


def get_participants_data_source_sync_timestamps(db_user, db_campaign, db_data_source):
	session = get_db_connection()
	res = session.execute(f'select "syncTimestamp" from "stats"."perDataSourceStats" where "campaignId"=%s and "userId"=%s and "dataSourceId"=%s allow filtering;', (
		db_campaign.id,
		db_user.id,
		db_data_source.id,
	))
	return 0 if res is None else res.syncTimestamp


def get_filtered_amount_of_data(db_campaign, from_timestamp=0, till_timestamp=9999999999999, db_user=None, db_data_source=None):
	session = get_db_connection()
	amount = 0

	if db_user is None:
		# all users
		if db_data_source is None:
			# all data sources
			for db_participant_user in get_campaign_participants(db_campaign=db_campaign):
				amount += session.execute(f'select count(*) from "data"."{db_campaign.id}-{db_participant_user.id}" where "timestamp">=%s and "timestamp"<%s allow filtering;', (
					from_timestamp,
					till_timestamp
				)).one()[0]
		else:
			# single data source
			for db_participant_user in get_campaign_participants(db_campaign=db_campaign):
				amount += session.execute(f'select count(*) from "data"."{db_campaign.id}-{db_participant_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s allow filtering;', (
					db_data_source.id,
					from_timestamp,
					till_timestamp
				)).one()[0]
	else:
		# single user
		if db_data_source is None:
			# all data sources
			amount += session.execute(f'select count(*) from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "timestamp">=%s and "timestamp"<%s;', (
				from_timestamp,
				till_timestamp
			)).one()[0]
		else:
			# single data source
			# f'select count(*) as "amount" from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"={db_data_source["id"]} and "timestamp">={from_timestamp} and "timestamp"<{till_timestamp};'
			amount += session.execute(f'select count(*) from "data"."cmp{db_campaign.id}_usr{db_user.id}" where "dataSourceId"=%s and "timestamp">=%s and "timestamp"<%s allow filtering;', (
				db_data_source.id,
				from_timestamp,
				till_timestamp
			)).one()[0]
	return amount

# endregion
