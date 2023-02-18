'''Utility functions for the dashboard app.'''

from easytrack import models as mdl
from django.core.files.uploadedfile import TemporaryUploadedFile
import pandas as pd


def file_is_valid(data_source: mdl.DataSource, fp: TemporaryUploadedFile):
    """
    Checks if the columns in the file are the same as the columns in the data source
    :param dataSource: The data source
    :param fileContent: The file content
    :return: True if the columns are the same, False otherwise
    """

    # get data source configurations
    columns = []
    type_map = {
        'timestamp': {int},
        'text': {str},
        'integer': {int},
        'float': {int, float},
    }
    for item in sorted(data_source.configurations, key=lambda x: x['index']):
        columns.append((item['name'].lower(), type_map[item['type']]))

    # load fileContent string into a pandas dataframe (load string, not file)
    df = pd.read_csv(fp)

    # check validity
    is_valid = True
    column_comparisons = list(zip(columns, df.columns))
    for req_col, df_col in column_comparisons:
        expected_col_name, acceptable_col_types = req_col

        print('expected', f'{expected_col_name}({acceptable_col_types})',
              'actual', f'{df_col}({df.dtypes[df_col]})')

        if df_col != expected_col_name or df.dtypes[
                df_col] not in acceptable_col_types:
            is_valid = False
            break

    return is_valid
