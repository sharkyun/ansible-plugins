#coding:utf-8
# (C) 2020,闫顺军, <sharkyunops@126.com>
# (c) 2020 Ansible Custom Plugin Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: mysql_plays
    type: notification
    short_description: 将 playbook 的执行结果输出到 MySQL 中。
    version_added: historical
    description:
      - 这个回调插件将会把输出存入 MySQL 服务器中。
    requirements:
     - 需要配置到 ansible.cfg 中 Whitelist
     - 可以被访问的 MySQL 服务器实例
     - Python 版本对应的 pymysql 或者 mysqlclient 模块
     - 创表语句
       create table playsresult(
         id int auto_increment primary key,
         user varchar(16) not null,
         host varchar(32) not null,
         category varchar(11) not null,
         result text,
         create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    options:
      mysql_host:
        version_added: '2.9'
        default: locallhost
        description: MySQL 服务器 IP或者主机名.
        env:
          - name: ANSIBLE_MYSQL_HOST
        ini:
          - section: callback_mysql_plays
            key: mysql_host
      mysql_port:
        version_added: '2.9'
        default: 3306
        description: MySQL 服务器监听端口.
        env:
          - name: ANSIBLE_MYSQL_PORT
        ini:
          - section: callback_mysql_plays
            key: mysql_port
        type: int
      mysql_user:
        version_added: '2.9'
        default: ansible
        description: MySQL 服务器登录用户.
        env:
          - name: ANSIBLE_MYSQL_USER
        ini:
          - section: callback_mysql_plays
            key: mysql_user
      mysql_password:
        version_added: '2.9'
        default: 'QFedu123!'
        description: MySQL 服务器登录用户.
        env:
          - name: ANSIBLE_MYSQL_PASSWORD
        ini:
          - section: callback_mysql_plays
            key: mysql_password
      mysql_db:
        version_added: '2.9'
        default: ansible
        description: 存放数据的库名称.
        env:
          - name: ANSIBLE_MYSQL_DB
        ini:
          - section: callback_mysql_plays
            key: db
      mysql_table:
        version_added: '2.9'
        default: playsresult
        description: 存放数据的表名称.
        env:
          - name: ANSIBLE_MYSQL_TABLE
        ini:
          - section: callback_mysql_plays
            key: mysql_table
'''

import os
import time
import json
import getpass

from ansible.module_utils.common._collections_compat import MutableMapping
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native


try:
    import MySQLdb as mysqldb
    pwd = "passwd"
except ImportError:
    try:
        import pymysql as mysqldb
        pwd = "password"
    except ImportError:
        raise AnsibleError("没有 pymysql 或 mysqlclient 包。")


# NOTE: in Ansible 1.2 or later general logging is available without
# this plugin, just set ANSIBLE_LOG_PATH as an environment variable
# or log_path in the DEFAULTS section of your ansible configuration
# file.  This callback is an example of per hosts logging for those
# that want it.


class CallbackModule(CallbackBase):
    """
    logs playbook results, per host, in /var/log/ansible/hosts
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'log_plays'
    CALLBACK_NEEDS_WHITELIST = True

    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    MSG_FORMAT = "%(now)s - %(category)s - %(data)s\n\n"

    def __init__(self):

        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.mysql_host = self.get_option("mysql_host")
        self.mysql_port = self.get_option("mysql_port")
        self.mysql_user = self.get_option("mysql_user")
        self.mysql_password = self.get_option("mysql_password")
        self.mysql_db = self.get_option("mysql_db")
        self.mysql_table = self.get_option("mysql_table")

        self.user = getpass.getuser()

    def _mysql(self):
        db_conn={"host": self.mysql_host,
                 "port": self.mysql_port,
                 "user": self.mysql_user,
                 pwd: self.mysql_password,
                 "db": self.mysql_db}

        print("==>", self.mysql_host)
        print("==>", self.mysql_password)
        db = mysqldb.connect(**db_conn)

        cursor= db.cursor()

        return db, cursor


    def _execute_sql(self, host, category, data):
        if isinstance(data, MutableMapping):
            if '_ansible_verbose_override' in data:
                # avoid logging extraneous data
                data = 'omitted'
            else:
                data = data.copy()
                invocation = data.pop('invocation', None)
                data = json.dumps(data, cls=AnsibleJSONEncoder)
                if invocation is not None:
                    data = json.dumps(invocation) + " => %s " % data

        sql = """
              insert into {}(host,user,category,result)
              values(%s,%s,%s,%s)
              """.format(self.mysql_table)

        db, cursor = self._mysql()

        try:
            cursor.execute(sql, (host, self.user, category, data))
            db.commit()
        except Exception as e:
            raise AnsibleError("%s" % to_native(e))
        finally:
            cursor.close()
            db.close()



    def runner_on_failed(self, host, res, ignore_errors=False):
        self._execute_sql(host, 'FAILED', res)

    def runner_on_ok(self, host, res):
        self._execute_sql(host, 'OK', res)

    def runner_on_skipped(self, host, item=None):
        self._execute_sql(host, 'SKIPPED', '...')

    def runner_on_unreachable(self, host, res):
        self._execute_sql(host, 'UNREACHABLE', res)

    def runner_on_async_failed(self, host, res, jid):
        self._execute_sql(host, 'ASYNC_FAILED', res)

    def playbook_on_import_for_host(self, host, imported_file):
        self._execute_sql(host, 'IMPORTED', imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self._execute_sql(host, 'NOTIMPORTED', missing_file)
