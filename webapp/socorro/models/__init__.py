from sqlalchemy import *
from sqlalchemy.ext.assignmapper import assign_mapper
from sqlalchemy.ext.selectresults import SelectResultsExt

from pylons.database import session_context
from datetime import datetime

meta = DynamicMetaData()

"""
Define database structure.

The crash reports table is a parent table that all reports partitions inherit.  No
data is actually stored in this table.  If it is, we have a problem.

Check constraints will be placed on reports to ensure this doesn't happen.  See
the PgsqlSetup class for how partitions and check constraints are set up.
"""
reports_table = Table('reports', meta,
  Column('id', Integer, primary_key=True, autoincrement=True),
  Column('date', DateTime),
  Column('uuid', String(50), index=True),
  Column('product', String(20)),
  Column('version', String(10)),
  Column('build', String(10)),
  Column('signature', String(50), index=True),
  Column('url', String(255), index=True),
  Column('install_age', Integer),
  Column('last_crash', Integer),
  Column('comments', String(500)),
  Column('cpu_name', String(50)),
  Column('cpu_info', String(50)),
  Column('reason', String(50)),
  Column('address', String(10)),
  Column('os_name', String(50)),
  Column('os_version', String(50))
)

frames_table = Table('frames', meta,
  Column('report_id', Integer, ForeignKey('reports.id'), primary_key=True),
  Column('thread_num', Integer, primary_key=True),
  Column('frame_num', Integer, nullable=False),
  Column('module_name', String(20)),
  Column('function', String(100)),
  Column('source', String(200)),
  Column('source_line', Integer),
  Column('instruction', String(10))
)

dumps_table = Table('dumps', meta,
  Column('report_id', Integer, ForeignKey('reports.id'), primary_key=True),
  Column('data', String(50000))
)

"""
Indexes for our tables based on commonly used queries (subject to change!).

Manual index naming conventions:
  idx_table_col1_col2_col3

Note:
  Many indexes can be defined in table definitions, and those all start with
  "ix_".  Indexes we set up ourselves use "idx" to avoid name conflicts, etc.
"""
# Top crashers index, for use with the top crasher reports query.
Index('idx_reports_product_version_build',reports_table.c.product, reports_table.c.version,
    reports_table.c.build)


def EmptyFilter(x):
  """Return None if the argument is an empty string, otherwise
     return the argument."""
  if x == '':
    return None
  return x

class Frame(object):
  def __str__(self):
    if self.report_id is not None:
      return str(self.report_id)
    else:
      return ""

  def readline(self, line):
    values = line.split("|")
    frame_data = dict(zip(['thread_num', 'frame_num', 'module_name',
                           'function', 'source', 'source_line', 'instruction'],
                          map(EmptyFilter, line.split("|"))))
    self.__dict__.update(frame_data)


class Report(object):
  def __init__(self):
    self.date = datetime.now()

  def __str__(self):
    if self.report_id is not None:
      return str(self.report_id)
    else:
      return ""

  def read_header(self, fh):
    for line in fh:
      line = line[:-1]
      # empty line separates header data from thread data
      if line == '':
        break
      values = line.split("|")
      if values[0] == 'OS':
        self.os_name = values[1]
        self.os_version = values[2]
      elif values[0] == 'CPU':
        self.cpu_name = values[1]
        self.cpu_info = values[2]
      elif values[0] == 'Crash':
        self.reason = values[1]
        self.address = values[2]

class Dump(object):
  def __str__(self):
    if self.report_id is not None:
      return str(self.report_id)
    else:
      return ""

"""
This defines our relationships between the tables assembled above.  It has to be
near the bottom since it uses the objects defined after the table definitions.
"""
frame_mapper = assign_mapper(session_context, Frame, frames_table)
report_mapper = assign_mapper(session_context, Report, reports_table, 
  properties = {
    'frames': relation(Frame, lazy=True, cascade="all, delete-orphan", 
                     order_by=[frames_table.c.thread_num, frames_table.c.frame_num]),
    'dumps': relation(Dump, lazy=True, cascade="all, delete-orphan")
  }
)
dump_mapper = assign_mapper(session_context, Dump, dumps_table)
