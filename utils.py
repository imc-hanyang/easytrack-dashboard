from typing import Any
import tempfile
from os.path import join, exists
from os import mkdir, chmod


def replacenull(
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


def notnull(
	value: Any
) -> Any:
	"""
	Asserts that a provided argument is not None
	:param value: value being checked
	:return: value if it is not None
	"""

	assert value is not None
	return value


def get_temp_filepath(
	filename: str
) -> str:
	"""
	Validates presence of a temporary directory, and opens a file for writing in the directory.
	:param filename: filename for writing
	:return: path to the file
	"""

	root = join(tempfile.gettempdir(), 'easytrack_dashboard')
	if not exists(root):
		mkdir(root)
		chmod(root, 0o777)

	res = join(
		root,
		notnull(filename)
	)
	fp = open(res, 'w+', encoding='utf8')
	fp.close()

	return res
