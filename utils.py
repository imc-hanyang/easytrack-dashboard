from typing import Any


def replaceIfNone(
	value: Any,
	replacement: Any
):
	"""
	Validate that a provided argument is not None, replace if so.
	Raises a ValueError if both value and replacement are None.
	:param value: value being checked for None
	:param replacement: replacement if value is None
	:return: value or replacement depending on value's content
	"""
	if value is None:
		if replacement is None:
			raise ValueError(f'replacement value cannot be {None}')
		else:
			return replacement  # is None
	else:
		return value  # is not None


def failIfNone(
	value: Any
) -> Any:
	"""
	Asserts that a provided argument is not None
	:param value: value being checked
	:return: value if it is not None
	"""
	assert value is not None
	return value
