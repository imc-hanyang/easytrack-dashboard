from __future__ import annotations
from typing import List

# app
from orm.models import User, Campaign, Participant, Supervisor, DataSource, CampaignDataSources
from utils import failIfNone


def find_user(
	user_id: int,
	email: str
) -> User | None:
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
		failIfNone(None)  # both user_id and email are None


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
		campaign=failIfNone(campaign),
		user=failIfNone(user)
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
		campaign=failIfNone(campaign),
		user=failIfNone(user)
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
		Participant.campaign == failIfNone(campaign)
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
		Participant.campaign == failIfNone(campaign)
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
		Supervisor.campaign == failIfNone(campaign)
	)


def get_campaign(
	campaign_id: int
) -> Campaign | None:
	"""
	Used for finding Campaign object by id.
	:param campaign_id: id of campaign being queried
	:return: Campaign object
	"""

	return Campaign.get_or_none(
		id=failIfNone(campaign_id)
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
		Supervisor.select().where(Supervisor.user == failIfNone(user))
	))


def find_data_source(
	data_source_id: int,
	name: str = None,
) -> DataSource | None:
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
		failIfNone(None)  # both data_source_id and name are None


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
		CampaignDataSources.select().where(CampaignDataSources.campaign == failIfNone(campaign))
	))
