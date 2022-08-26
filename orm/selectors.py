from typing import List, Optional
from datetime import datetime as dt

# app
from orm.models import User, Campaign, Participant, Supervisor, DataSource, CampaignDataSources, DataTable, DataRecord
from utils import notnull


def find_user(
	user_id: int,
	email: str
) -> Optional[User]:
	"""
	Used for finding User object by either id or email.
	:param user_id: id of user being queried
	:param email: email of user being queried
	:return: User object
	"""

	if user_id is not None:
		return User.get_or_none(id=user_id)
	elif email is not None:
		return User.get_or_none(email=email)
	else:
		notnull(None)  # both user_id and email are None


def is_participant(
	user: User,
	campaign: Campaign
) -> bool:
	"""
	Checks whether a user is a campaign's participant or not
	:param user: user being checked
	:param campaign: campaign being checked
	:return: true if user is campaign's participant, false if not
	"""

	return Participant.select().where(
		campaign=notnull(campaign),
		user=notnull(user)
	).exists()


def is_supervisor(
	user: User,
	campaign: Campaign
) -> bool:
	"""
	Checks whether a user is a campaign's supervisor or not
	:param user: user being checked
	:param campaign: campaign being checked
	:return: true if user is campaign's supervisor, false if not
	"""

	return Supervisor.select().where(
		campaign=notnull(campaign),
		user=notnull(user)
	).exists()


def get_campaign_participants(
	campaign: Campaign
) -> List[Participant]:
	"""
	Returns list of participants of a campaign
	:param campaign: campaign being queried
	:return: list of campaign's participants
	"""

	return Participant.select().where(
		Participant.campaign == notnull(campaign)
	)


def get_campaign_participants_count(
	campaign: Campaign
) -> int:
	"""
	Returns count of participants of a campaign
	:param campaign: campaign being queried
	:return: number of campaign's participants
	"""

	return Participant.select().where(
		Participant.campaign == notnull(campaign)
	).count()


def get_campaign_supervisors(
	campaign: Campaign
) -> List[Supervisor]:
	"""
	Returns list of a campaign's supervisors
	:param campaign: campaign being queried
	:return: list of campaign's supervisors
	"""

	return Supervisor.select().where(
		Supervisor.campaign == notnull(campaign)
	)


def get_campaign(
	campaign_id: int
) -> Optional[Campaign]:
	"""
	Used for finding Campaign object by id.
	:param campaign_id: id of campaign being queried
	:return: Campaign object
	"""

	return Campaign.get_or_none(
		id=notnull(campaign_id)
	)


def get_supervisor_campaigns(
	user: User
) -> List[Campaign]:
	"""
	Filter campaigns by supervisor (when researcher wants to see the list of their campaigns)
	:param user: the supervisor
	:return: list of supervisor's campaigns
	"""

	return list(map(
		lambda supervisor: supervisor.campaign,
		Supervisor.select().where(Supervisor.user == notnull(user))
	))


def find_data_source(
	data_source_id: int,
	name: str = None,
) -> Optional[DataSource]:
	"""
	Used for finding DataSource object by either id or name.
	:param data_source_id: id of data source being queried
	:param name: name of data source being queried
	:return: DataSource object (if found)
	"""

	if data_source_id is not None:
		return DataSource.get_or_none(id=data_source_id)
	elif name is not None:
		return DataSource.get_or_none(name=name)
	else:
		notnull(None)  # both data_source_id and name are None


def get_all_data_sources() -> List[DataSource]:
	"""
	List of all data sources in database
	:return: the list of data sources
	"""

	return DataSource.select()


def get_campaign_data_sources(
	campaign: Campaign
) -> List[DataSource]:
	"""
	Returns list of a campaign's data sources
	:param campaign: campaign being queried
	:return: list of campaign's data sources
	"""

	return list(map(
		lambda campaign_data_source: campaign_data_source.data_source,
		CampaignDataSources.select().where(CampaignDataSources.campaign == notnull(campaign))
	))


def get_next_k_data_records(
	participant: Participant,
	data_source: DataSource,
	from_ts: dt,
	k: int
) -> List[DataRecord]:
	"""
	Retrieves next k data records from database
	:param participant: participant that has refernece to user and campaign
	:param data_source: type of data to retrieve
	:param from_ts: starting timestamp
	:param k: max amount of records to query
	:return: list of data records
	"""

	return DataTable.select_next_k(
		participant=notnull(participant),
		data_source=notnull(data_source),
		from_ts=notnull(from_ts),
		limit=notnull(k)
	)


def get_filtered_data_records(
	participant: Participant,
	data_source: DataSource,
	from_ts: dt = None,
	till_ts: dt = None
) -> List[DataRecord]:
	"""
	Retrieves filtered data based on provided range (start and end timestamps)
	:param participant: participant that has refernece to user and campaign
	:param data_source: type of data to retrieve
	:param from_ts: starting timestamp
	:param till_ts: ending timestamp
	:return: list of data records
	"""

	return DataTable.select_range(
		participant=notnull(participant),
		data_source=notnull(data_source),
		from_ts=notnull(from_ts),
		till_ts=notnull(till_ts)
	)
