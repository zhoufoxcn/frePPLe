#
# Copyright (C) 2007 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$
# email : jdetaeye@users.sourceforge.net

from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction
from django.conf import settings
from django.utils.translation import ugettext as _

from execute.models import log


class Command(BaseCommand):
  help = '''
  This command empties the contents of all data tables in the frePPLe database.

  The results are similar to the 'flush input output' command, except that the
  database objects are not dropped and recreated.
  Another difference is that the initial_data fixture is not loaded.
  '''
  option_list = BaseCommand.option_list + (
      make_option('--user', dest='user', default='',
          type='string', help='User running the command'),
      )

  requires_model_validation = False

  def get_version(self):
    return settings.FREPPLE_VERSION

  @transaction.commit_manually
  def handle(self, **options):
    # Make sure the debug flag is not set!
    # When it is set, the django database wrapper collects a list of all sql
    # statements executed and their timings. This consumes plenty of memory
    # and cpu time.
    tmp_debug = settings.DEBUG
    settings.DEBUG = False

    log(category='ERASE', user=options['user'],
      message=_('Start erasing the database')).save()
    try:
      cursor = connection.cursor()
      # SQLite specials
      if settings.DATABASE_ENGINE == 'sqlite3':
        cursor.execute('PRAGMA synchronous = OFF')  # Performance improvement
      # Delete all records from the tables
      sql_list = connection.ops.sql_flush(no_style(), [
        'out_problem','out_flowplan','out_loadplan','out_demandpegging',
        'out_operationplan','demand','forecastdemand','forecast','flow',
        'resourceload','buffer','resource','operationplan','item','suboperation',
        'operation','location','bucket','calendar','customer'
        ], [] )
      for sql in sql_list:
        cursor.execute(sql)
        transaction.commit()
      # SQLite specials
      if settings.DATABASE_ENGINE == 'sqlite3':
        cursor.execute('vacuum')   # Shrink the database file
      log(category='ERASE', user=options['user'],
        message=_('Finished erasing the database')).save()
    except Exception, e:
      log(category='RUN', user=options['user'],
        message=u'%s: %s' % (_('Failed erasing the database'),e)).save()
      raise e
    finally:
      transaction.commit()
      settings.DEBUG = tmp_debug