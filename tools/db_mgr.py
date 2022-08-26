from subprocess import PIPE
from tools import settings
from tools import utils
import subprocess
import json


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
