# User Guide

In order to use Kirby, you will need several services running.
The web interface is the only component that needs access to the database.

## Kirby managed services

- the `kirby` web UI, to configure your Kirby cluster
- **at least one**  `kirby` supervisor to trigger jobs and execute them

.. note:: We recommend using your operating system process supervisor 
          such as `systemd` to run `kirby`. 
          
.. todo:: provide systemd templates

## Supporting services

- a Kafka cluster (required by all `kirby` services)
- a database server (required for the `kirby` web UI)

.. note:: Running both services on the same machine is fine for development


## Installing Kirby

```bash
$ pip install -U kirby
```

## Running the web interface

```bash
$ kirby web [--host 127.0.0.1] [--port 8080]
```

.. important:: We recommend you not to expose the web service directly on the Internet, but to use a reverse proxy such as `Nginx <http://nginx.org/>`_ or `HAProxy <http://www.haproxy.org>`_


### Adding a superuser

If you want to add a local user (so not using external user provisioning like 
LDAP or Okta), you can use the following command on the web UI server

```bash
$ kirby demo
demo data inserted in the database
```

### Demonstration database

If you just want a quick preview of Kirby's features, you can summon the demo
database as follows:

.. warning:: Please only use on an empty database, it will mess with your 
   existing data and there is no rollback mechanism.

```bash
$ kirby adduser alice
Password: ******
Give admin rights? [y/N]: y
User alice added with admin rights
```

## Running the supervisor

.. important:: - There must be at least one `supervisor` instance running at all times.
               - Each supervisor must have a unique name
  
If you want to call your instance "server-1" then start kirby as follows:

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
