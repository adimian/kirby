.. _linking-userguide:
# User Guide

`kirby` is a Python Frameworks which manages user's 
scripts execution on several servers. User's scripts can be :
- scheduled script (schedule definition is based on `cron`)
- daemon script

Scripts are run on several servers (`kirby supervisors`). In order to ensure 
that a scheduled script is never launched twice, Kirby uses `Kafka` topics. 

## Kirby dependencies
`Kirby` uses a `redis` server for the leader election process (see below). Before 
running `kirby`, start a `redis` server : 
```bash
$ redis-server
```
As explained above `kirby` also needs a `Kafka` cluster (required by all `kirby` services)

```bash
$ bin/zookeeper-server-start.sh config/zookeeper.properties
$ bin/kafka-server-start.sh config/server.properties
```
Finally, `kirby` needs a database server (required for the `kirby` web UI). 



## Installing Kirby
Use `pip` to install `kirby` : 

```bash
$ pip install -U kirby
```

## Environment variables 
The following environment variables are used by `kirby` :

| Variable name                   | Content description                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------|
| `SQLALCHEMY_DATABASE_URI`         | Path for `kirby` db storage. Example : `///kirby.db`                                    |
| `SQLALCHEMY_TRACK_MODIFICATIONS`  | `Flask` app parameter **(Default=None)**                                                                 |
| `SECRET_KEY`                      | `Flask` app parameter : secret key for session.                                                                  |
| `SECURITY_PASSWORD_SALT`          | `Flask` app parameter                                                                 |
|`TESTING`                          | `Flask` app parameter  |
| `KAFKA_BOOTSTRAP_SERVERS`         | `kafka` Bootstrap server (Example :127.0.0.1:9092)                                                                      |
| `KAFKA_USE_SSL`                   | `kafka` parameter : tells if SSL is used                                                      |
| `KAFKA_SSL_CAFILE`                | `kafka` parameter :  `ssl_cafile`                                               |
| `KAFKA_SSL_CERTFILE`              | `kafka` parameter  : see `ssl_certfile`                                            |
| `KAFKA_SSL_KEYFILE`               | `kafka` parameter  :see `ssl_keyfile`                                                    |
| `KIRBY_TOPIC_SCHEDULED_JOBS`          | Scheduled job offers `kafka` topic name **(Default: `.kirby.job-offers.scheduled`)**                              |
| `KIRBY_TOPIC_DAEMON_JOBS`          | Daemon job offers `kafka` topic name **(Default: `.kirby.job-offers.daemon` )**                            |                                    |
| `KIRBY_SCHEDULE_ENDPOINT`         | `kirby` web server followed schedule endpoint. For example :http://127.0.0.1:8080/schedule |
|`EXT_WAIT_BETWEEN_RETRIES`   |  see `tenacity.retry` wait argument **(Default=0.4)** |
|`EXT_RETRIES`   |  see `tenacity.retry` stop argument **(Default=3)**|
|`LOG_FORMAT`   | see format parameter in `logging.basicConfig()` **(Default= "[%(asctime)s] %(levelname)s:%(name)s:%(message)s")** |

## Adding a superuser

If you want to add a local user (so not using external user provisioning like 
`LDAP` or `Okta`), you can use the following command on the web UI server

```bash
$ kirby adduser alice
Password: ******
Give admin rights? [y/N]: y
User alice added with admin rights
```
## Script database creation
The goal of `kirby` is to manage user's scripts execution. `kirby` input is 
therefore a script database following this model.

.. todo:: add link to database model.

Database can be created and modified in `kirby` Web interface or through a `json` file. 
Two examples of `json` files are available in Kirby code : 
- `demo.json`
- `short_demo.json`

Use `demo` command to import one of those two `json` files in the `kirby` script database.

```bash
$ kirby demo
demo data inserted in the database
```
or 
```bash
$ kirby demo --json_file_path /home/user/my_kirby_path/short_demo.json
demo data inserted in the database
```

.. warning:: Please only use on an empty database, it will mess with your 
   existing data and there is no rollback mechanism.
   

## Kirby web interface
`kirby` web interface has two main functions: 
- Interact with the `kirby` script database (visualization and modification),
- Follow (in live mode) scripts execution (`logs` tab). 
 
Run the web interface with following command :
```bash
$ kirby web [--host 127.0.0.1] [--port 8080]
```

.. important:: We recommend you not to expose the web service directly on the 
Internet, but to use a reverse proxy such as `Nginx <http://nginx.org/>`_ or
 `HAProxy <http://www.haproxy.org>`_


## Running a `pypi` server
As mentioned above, package names (and versions) of scripts to be run are stored 
in `kirby` database.
Once it is time to run a script, `kirby` fetches those packages from `Pypi`. 
In case user doesn't 
want to set his script on `Pypi.org`, it is easy to run a local `pypiserver` :
https://pypi.org/project/pypiserver/
This step is mandatory. If scripts are note set on a `pypi` server, they will not be run. 


## Create job-offers topics and running supervisors
Several `supervisor` can be run. One of those is called the leader. 
Leader `supervisor` is the only one which fetches jobs to run from the `kirby` 
script database and send them to  the appropriate `job-offers` Kafka topic (
`KIRBY_TOPIC_SCHEDULED_JOBS` or `KIRBY_TOPIC_DAEMON_JOBS`)

All `supervisor` (including leader) consume scripts in those Kafka topics, create 
the Python virtual environments, install the scripts from `Pypiserver` 
and run them (in a separated subprocess).
If leader `supervisor` crashes, another `supervisor` will take the lead.

.. important:: - There must be at least one `supervisor` instance running at all times.
               - Each supervisor must have a unique name

If you want to run several supervisors, it is mandatory to create previously the 
`job-offers` Kafka topics with a number of partitions higher or equals to the 
number of supervisors you want to run. If you don't know how many supervisors
you want to run, just create the topics with enough partitions (10 for example):

```bash
$ kafka-topics --create --zookeeper localhost:2181 --replication-factor 1 --partitions 10 --topic KIRBY_TOPIC_SCHEDULED_JOBS
$ kafka-topics --create --zookeeper localhost:2181 --replication-factor 1 --partitions 10 --topic KIRBY_TOPIC_DAEMON_JOBS
```

If you want to call your instance "server-1" then start `kirby`  as follows:

```bash
$ kirby supervisor server-1 [--window 5] [--wakeup 30]
```
- `window` is the frequency at which the supervisor tries to elect itself as the 
cluster leader. Use longer interval if your network is too noisy 
and you do not have scheduled jobs.
   
- `wakeup` is the shortest interval between two scheduled jobs. Use longer interval 
if your network is limited and you do not have scheduled jobs or 
if the intervals are very long. 
   
.. note:: Defaults are fine in most cases.   
