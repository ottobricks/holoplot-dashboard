# -*- coding: utf-8 -*-

import os

from bokeh.layouts import column
from bokeh.models import ColumnDataSource
from bokeh.models import HoverTool
from bokeh.models.widgets import CheckboxButtonGroup
from bokeh.models.widgets import Div
from bokeh.plotting import figure
from bokeh.plotting import curdoc

import pandas as pd

##############################################################
#                                                            #
#             D  A  T  A     L  O  A  D  I  N  G             #
#                                                            #
##############################################################

kickstarter_df = pd.read_csv(os.path.join('..', 'kickstarter-cleaned.csv'), parse_dates=True)
kickstarter_df['broader_category'] = kickstarter_df['category_slug'].str.split('/').str.get(0)
kickstarter_df['created_at'] = pd.to_datetime(kickstarter_df['created_at'])

kickstarter_df_sub = kickstarter_df.sample(10000)


CATEGORIES = kickstarter_df['broader_category'].unique()
COLUMNS = ['launched_at', 'deadline', 'blurb', 'usd_pledged', 'state', 'spotlight', 'staff_pick', 'category_slug', 'backers_count', 'country']
# Picked with http://tristen.ca/hcl-picker/#/hlc/6/1.05/251C2A/E98F55
COLORS = ['#7DFB6D', '#C7B815', '#D4752E', '#C7583F']
STATES = ['successful', 'suspended', 'failed', 'canceled']

title = Div(text='<h1 style="text-align: center">Kickstarter Dashboard</h1>')

# This looks better than the multiselect widget
select = CheckboxButtonGroup(labels=CATEGORIES.tolist())

layout = column(title, select, sizing_mode='scale_width')

curdoc().add_root(layout)
