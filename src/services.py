from datetime import datetime as dt
from typing import Dict, List, Optional

# app
from src.data import models
from src.data import wrappers
from src.selectors import is_participant, is_supervisor, find_data_source
from utils import notnull


def create_user(
	email: str,
	name: str,
	session_key: str
) -> models.User:
	"""
	Creates a user object in database and returns User object
	:param email: email of new user
	:param name: name of new user
	:param session_key: session_key for the new user
	:return:
	"""

	return models.User.create(
		email=notnull(email),
		name=notnull(name),
		session_key=notnull(session_key)
	)


def set_user_session_key(
	user: models.User,
	new_session_key: str
) -> None:
	"""
	Updates a user's session key (that is used for authentication)
	:param user: the user
	:param new_session_key: new session key
	:return: None
	"""

	user.session_key = notnull(new_session_key)
	user.save()


def add_participant_to_campaign(
	add_user: models.User,
	campaign: models.Campaign
) -> bool:
	"""
	Binds user with campaign, making a participant.
	After binding is done, creates a new Data table for storing the participant's data.
	:param add_user: User object to be bound to a campaign
	:param campaign: Campaign object that user binds with
	:return: whether user has been bound
	"""

	if is_participant(
		user=notnull(add_user),
		campaign=notnull(campaign)
	): return False

	# 1. bind the user to campaign
	participant = models.Participant.create(
		campaign=campaign,
		user=add_user
	)

	# 2. create a new data table for the participant
	wrappers.DataTable.create(
		participant=participant
	)

	return True


def add_supervisor_to_campaign(
	new_user: models.User,
	supervisor: models.Supervisor,
) -> bool:
	"""
	Binds user with campaign, making a supervisor.
	:param new_user: User object to be bound to a campaign as a supervisor
	:param supervisor: Supervisor object that has reference to campaign (initially the owner is the first supervisor)
	:return: whether user has been bound (as supervisor)
	"""

	campaign: models.Campaign = notnull(supervisor).campaign

	if is_supervisor(
		user=notnull(new_user),
		campaign=notnull(campaign)
	): return False

	models.Supervisor.create(
		campaign=campaign,
		user=new_user
	)
	return True


def remove_supervisor_from_campaign(
	oldSupervisor: models.Supervisor
) -> None:
	"""
	Unbinds a (supervisor) user from campaign.
	:param oldSupervisor: supervisor representing the binding between a user and a campaign.
	:return: None
	"""

	campaign: models.Campaign = notnull(oldSupervisor).campaign
	if oldSupervisor.user != campaign.owner: oldSupervisor.delete()


def create_campaign(
	owner: models.User,
	name: str,
	start_ts: dt,
	end_ts: dt
) -> models.Campaign:
	"""
	Creates a campaign object in database and returns Campaign object
	:param owner: owner (User instance) of the new campaign
	:param name: title of the campaign
	:param start_ts: when campaign starts
	:param end_ts: when campaign ends
	:return: newly created Campaign instance
	"""

	# 1. create a campaign
	campaign = models.Campaign.create(
		owner=notnull(owner),
		name=notnull(name),
		start_ts=notnull(start_ts),
		end_ts=notnull(end_ts)
	)

	# 2. add owner as a supervisor
	models.Supervisor.create(
		campaign=campaign,
		user=owner
	)

	return campaign


def update_campaign(
	supervisor: models.Supervisor,
	name: str,
	start_ts: dt,
	end_ts: dt
) -> None:
	"""
	Update parameters of a campaign object in the database.
	:param supervisor: supervisor of the campaign (includes reference to user and campaign)
	:param name: title of the campaign
	:param start_ts: when campaign starts
	:param end_ts: when campaign ends
	:return: newly created Campaign instance
	"""

	campaign: models.Campaign = notnull(supervisor).campaign
	campaign.name = notnull(name)
	campaign.start_ts = notnull(start_ts)
	campaign.end_ts = notnull(end_ts)
	campaign.save()


def delete_campaign(
	supervisor: models.Supervisor
) -> None:
	"""
	Delete a campaign - must only be called if campaign's owner makes the call.
	:param supervisor: supervisor of the campaign (includes reference to user and campaign)
	:return: None
	"""

	campaign: models.Campaign = notnull(supervisor).campaign
	if supervisor.user == campaign.owner: campaign.delete()


def create_data_source(
	name: str,
	icon_name: str
) -> None:
	"""
	Creates a data source (if not exists)
	:param name: name of the data source
	:param icon_name: icon of the data source
	:return: None
	"""

	if models.DataSource.get_or_none(
		name=notnull(name)
	): return

	models.DataSource.create(
		name=name,
		icon_name=notnull(icon_name)
	)


def create_data_record(
	participant: models.Participant,
	data_source: models.DataSource,
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

	wrappers.DataTable.insert(
		participant=participant,
		data_source=data_source,
		ts=ts,
		val=val
	)


def create_data_records(
	participant: models.Participant,
	data_source_ids: List[int],
	tss: List[dt],
	vals: List[Dict]
) -> None:
	"""
	Creates a data record in raw data table (e.g. sensor reading)
	:param participant: participant of a campaign
	:param data_source_ids: data sources of the data records
	:param tss: timestamps
	:param vals: values
	:return: None
	"""

	data_sources: Dict[int, models.DataSource] = dict()
	for ts, data_source_id, val in zip(tss, data_source_ids, vals):
		if data_source_id not in data_sources:
			db_data_source = find_data_source(data_source_id=data_source_id, name=None)
			if db_data_source is None: continue
			data_sources[data_source_id] = db_data_source
		create_data_record(
			participant=participant,
			data_source=data_sources[data_source_id],
			ts=ts,
			val=val
		)


def dump_data(
	participant: models.Participant,
	data_source: Optional[models.DataSource]
) -> str:
	"""
	Dumps content of a particular DataTable into a downloadable file
	:param participant: participant that has reference to user and campaign
	:param data_source: which data source to dump
	:return: path to the downloadable file
	"""

	return wrappers.DataTable.dump_to_file(
		participant=notnull(participant),
		data_source=data_source
	)
