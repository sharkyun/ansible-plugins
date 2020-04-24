### 1 保存插件到有效的目录下

把插件保存为 `mysql_plays.py` 文件，并存到ansible 控制节点的如下目录下: `~/.ansible/plugins/callback/`

```shell
[root@qfedu.com ~]# pwd
/root
[root@qfedu.com ~]# ls .ansible/plugins/callback/mysql_plays.py
.ansible/plugins/callback/mysql_plays.py
```



### 2开启使用插件

在 ansible.cfg 中编辑如下配置

```ini
callback_whitelist = mysql_plays
```

如果还使用了其他插件，请用英文的逗号分开。

比如

```ini
callback_whitelist = timer, mysql_plays
```

默认此插件仅对 playbook 生效，假如希望在 ad-hoc (快捷命令)中生效，继续打开如下配置，并职位 True

```ini
bin_ansible_callbacks = True
```



### 3 关于此插件的使用先决条件等信息

在做好以上步骤后，使用如下方式获取帮助

**验证配置的正确性**

```shell
[root@qfedu.com ~]# ansible-doc -t callback -l |grep mysql_plays
mysql_plays          将 playbook 的执行结果输出到 MySQL 中。
```

**查看帮助文档**

```shell
[root@qfedu.com ~]# ansible-doc -t callback  mysql_plays
> MYSQL_PLAYS    (/root/.ansible/plugins/callback/mysql_plays.py)

        这个回调插件将会把输出存入 MySQL 服务器中。

  * This module is maintained by The Ansible Community
OPTIONS (= is mandatory):

- mysql_db
        存放数据的库名称.
        [Default: ansible]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_DB
          ini:
          - key: db
            section: callback_mysql_plays

        version_added: 2.9

- mysql_host
        MySQL 服务器 IP或者主机名.
        [Default: locallhost]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_HOST
          ini:
          - key: mysql_host
            section: callback_mysql_plays

        version_added: 2.9

- mysql_password
        MySQL 服务器登录用户.
        [Default: QFedu123!]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_PASSWORD
          ini:
          - key: mysql_password
            section: callback_mysql_plays

        version_added: 2.9

- mysql_port
        MySQL 服务器监听端口.
        [Default: 3306]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_PORT
          ini:
          - key: mysql_port
            section: callback_mysql_plays

        type: int
        version_added: 2.9

- mysql_table
        存放数据的表名称.
        [Default: playsresult]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_TABLE
          ini:
          - key: mysql_table
            section: callback_mysql_plays

        version_added: 2.9

- mysql_user
        MySQL 服务器登录用户.
        [Default: ansible]
        set_via:
          env:
          - name: ANSIBLE_MYSQL_USER
          ini:
          - key: mysql_user
            section: callback_mysql_plays

        version_added: 2.9


REQUIREMENTS:  需要配置到 ansible.cfg 中 Whitelist, 可以被访问的 MySQL 服务器实例, Python 版本对应的 pymysql 或者
        mysqlclient 模块, 创表语句(注意:这里的表名需要根据选项中 mysql_table 的值一致) create table
        playsresult( id int auto_increment primary key, user varchar(16) not
        null, host varchar(32) not null, category varchar(11) not null, result
        text, create_time datetime NOT NULL DEFAULT CURRENT_TIMESTAMP );

        METADATA:
          status:
          - preview
          supported_by: community

TYPE: notification
```



### 4 配置插件使用的选项

关于限制条件

此插件已经有默认值，如果想修改需在 ansible.cfg 文件的最后添加如下配置

```ini
[callback_mysql_plays]
mysql_host = MySQL IP
mysql_port = MySQL 监听端口
mysql_user = MySQL 用户
mysql_password = MySQL 密码
mysql_db = MySQL 库名
mysql_table = MySQL 表名
```



### 5 执行 playbook



**playbook**

```yaml
- hosts: all
  gather_facts: no
  tasks:
  - name: test
    shell: date +"%F %T"
```

**Inventory**

```ini
[root@qfedu.com ~]#[dbservers]
172.18.0.3

[webservers]
172.18.0.4
172.18.0.5

[allservers:children]
dbservers
webservers
```



**执行playbook**

```shell
[root@qfedu.com ~]# ansible-playbook -i hosts remoteDate.yml

PLAY [all] *************************************************

TASK [test] *************************************************
fatal: [172.18.0.5]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: ssh: connect to host 172.18.0.5 port 22: Connection refused", "unreachable": true}
changed: [172.18.0.3]
changed: [172.18.0.4]

PLAY RECAP ************************************************************************************************************
172.18.0.3                 : ok=1    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.18.0.4                 : ok=1    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
172.18.0.5                 : ok=0    changed=0    unreachable=1    failed=0    skipped=0    rescued=0    ignored=0
```



**查询数据库**

> 为了输出效果，已对输出信息做成修改

```mysql
mysql> select * from playsresult\G
************ 11. row ************
         id: 21
       user: root
       host: 172.18.0.5
   category: UNREACHABLE
     result: {
     "msg": "Failed to connect to the host via ssh: ssh: connect to host 172.18.0.5 port 22: Connection refused", 
     "unreachable": true, 
     "changed": false}
create_time: 2020-04-24 01:34:46
************ 12. row ************
         id: 22
       user: root
       host: 172.18.0.3
   category: OK
     result: {
     "module_args": {"warn": true, 
                     "executable": null, 
                     "_uses_shell": true, 
                     "strip_empty_ends": true,
                     "_raw_params": "date +\"%F %T\"", 
                     "removes": null, 
                     "argv": null, 
                     "creates": null, 
                     "chdir": null, 
                     "stdin_add_newline": true, 
                     "stdin": null
                     }
     } => {"stderr_lines": [],
           "cmd": "date +\"%F %T\"", 
           "end": "2020-04-24 01:34:46.762027", 
           "_ansible_no_log": false,
           "stdout": "2020-04-24 01:34:46",
           "changed": true,
           "rc": 0,
           "start": "2020-04-24 01:34:46.518139",
           "stderr": "",
           "delta": "0:00:00.243888",
           "stdout_lines": ["2020-04-24 01:34:46"],
           "ansible_facts": {
           "discovered_interpreter_python": "/usr/bin/python"
           }
    }
create_time: 2020-04-24 01:34:46
************ 13. row ************
         id: 23
       user: root
       host: 172.18.0.4
   category: OK
     result: {
     "module_args": {"warn": true, 
                     "executable": null, 
                     "_uses_shell": true,                                      "strip_empty_ends": true,
                     "_raw_params": "date +\"%F %T\"",
                     "removes": null,
                     "argv": null,
                     "creates": null,
                     "chdir": null,
                     "stdin_add_newline": true,
                     "stdin": null
                     }
       } => {"stderr_lines": [], 
             "cmd": "date +\"%F %T\"",
             "end": "2020-04-24 01:34:46.767316", 
             "_ansible_no_log": false,
             "stdout": "2020-04-24 01:34:46", 
             "changed": true, 
             "rc": 0, 
             "start": "2020-04-24 01:34:46.528226",
             "stderr": "",
             "delta": "0:00:00.239090",
             "stdout_lines": ["2020-04-24 01:34:46"],
             "ansible_facts": {
             "discovered_interpreter_python": "/usr/bin/python"}
            }
create_time: 2020-04-24 01:34:46

```

