from datetime import datetime as dt
from typing import Dict

# app
from orm.models import User, Campaign, Participant, DataTable, Supervisor, DataSource
from orm.selectors import is_participant, is_supervisor
from utils import failIfNone


def create_user(
	email: str,
	name: str,
	session_key: str
) -> User:
	"""
	Creates a user object in database and returns User object
	:param email: email of new user
	:param name: name of new user
	:param session_key: session_key for the new user
	:return:
	"""

	return User.create(
		email=failIfNone(email),
		session_key=failIfNone(session_key),
		name=failIfNone(name),
	)


def set_user_session_key(
	user: User,
	new_session_key: str
) -> None:
	"""
	Updates a user's session key (that is used for authentication)
	:param user: the user
	:param new_session_key: new session key
	:return: None
	"""

	user.session_key = failIfNone(new_session_key)
	user.save()


def add_participant_to_campaign(
	add_user: User,
	campaign: Campaign
) -> bool:
	"""
	Binds user with campaign, making a participant.
	After binding is done, creates a new Data table for storing the participant's data.
	:param add_user: User object to be bound to a campaign
	:param campaign: Campaign object that user binds with
	:return: whether user has been bound
	"""

	if is_participant(
		user=failIfNone(add_user),
		campaign=failIfNone(campaign)
	): return False

	# 1. bind the user to campaign
	participant = Participant.create(
		campaign=campaign,
		user=add_user
	)

	# 2. create a new data table for the participant
	DataTable.create(
		participant=participant
	)

	return True


def add_supervisor_to_campaign(
	add_user: User,
	supervisor: Supervisor,
) -> bool:
	"""
	Binds user with campaign, making a supervisor.
	:param add_user: User object to be bound to a campaign as a supervisor
	:param supervisor: Supervisor object that has reference to campaign (initially the owner is the first supervisor)
	:return: whether user has been bound (as supervisor)
	"""

	campaign: Campaign = failIfNone(supervisor).campaign

	if is_supervisor(
		user=failIfNone(add_user),
		campaign=failIfNone(campaign)
	): return False

	Supervisor.create(
		campaign=campaign,
		user=add_user
	)
	return True


def remove_supervisor_from_campaign(
	supervisor: Supervisor
) -> None:
	"""
	Unbinds a (supervisor) user from campaign.
	:param supervisor: supervisor representing the binding between a user and a campaign.
	:return: None
	"""

	campaign: Campaign = failIfNone(supervisor).campaign
	if supervisor.user != campaign.owner: supervisor.delete()


def create_campaign(
	owner: User,
	name: str,
	start_ts: dt,
	end_ts: dt
) -> Campaign:
	"""
	Creates a campaign object in database and returns Campaign object
	:param owner: owner (User instance) of the new campaign
	:param name: title of the campaign
	:param notes: notes on the campaign
	:param start_ts: when campaign starts
	:param end_ts: when campaign ends
	:return: newly created Campaign instance
	"""

	# 1. create a campaign
	campaign = Campaign.create(
		owner=failIfNone(owner),
		name=failIfNone(name),
		start_ts=failIfNone(start_ts),
		end_ts=failIfNone(end_ts)
	)

	# 2. add owner as a supervisor
	Supervisor.create(
		campaign=campaign,
		user=owner
	)

	return campaign


def update_campaign(
	supervisor: Supervisor,
	name: str,
	start_ts: dt,
	end_ts: dt
) -> None:
	"""
	Update parameters of a campaign object in the database.
	:param supervisor: supervisor of the campaign (includes reference to user and campaign)
	:param name: title of the campaign
	:param notes: notes on the campaign
	:param start_ts: when campaign starts
	:param end_ts: when campaign ends
	:return: newly created Campaign instance
	"""

	campaign: Campaign = failIfNone(supervisor).campaign
	campaign.name = failIfNone(name)
	campaign.start_ts = failIfNone(start_ts)
	campaign.end_ts = failIfNone(end_ts)
	campaign.save()


def delete_campaign(
	supervisor: Supervisor
) -> None:
	"""
	Delete a campaign - must only be called if campaign's owner makes the call.
	:param supervisor: supervisor of the campaign (includes reference to user and campaign)
	:return: None
	"""

	campaign: Campaign = failIfNone(supervisor).campaign
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

	if DataSource.get_or_none(
		name=failIfNone(name)
	): return

	DataSource.create(
		name=name,
		icon_name=failIfNone(icon_name)
	)
