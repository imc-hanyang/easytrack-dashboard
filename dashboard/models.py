'''This module contains the models for the dashboard app.'''


class EnhancedDataSource:
    '''This class is a wrapper for a data source that has been enhanced with'''

    db_data_source: dict
    plot_str: str

    def __init__(self, db_data_source, plot_str=None):
        self.db_data_source = db_data_source
        self.plot_str = plot_str

    def attach_plot(self, plot_str):
        '''Attach a plot to this data source.'''
        self.plot_str = plot_str

    def id(self):
        '''Return the id of the data source.'''
        return self.db_data_source['id']

    def name(self):
        '''Return the name of the data source.'''
        return self.db_data_source['name']

    def icon_name(self):
        '''Return the icon name of the data source.'''
        return self.db_data_source['icon_name']

    def plot(self):
        '''Return the plot of the data source.'''
        return self.plot_str
