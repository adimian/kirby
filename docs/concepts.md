# Components

.. image:: _static/kirby-components.svg

Above is the diagram of all components of Kirby along with the dataflow and interprocess calls. Each and every one of
the components are described in the following.

It is highly recommended to understand how [Kafka](https://kafka.apache.org/) works in order to comprehend the components
of Kirby.

## Scripts

Kirby's task is to handle the execution of scripts that process data. 
The data which come from externals sources of Kirby should move between processes via Kafka topics. 

Currently as external sources, Kirby proposes support for `Web Services`,  `Topics` and `Files`.

User's Kafka topics are stored alongside  Kirby internal topics.

There are two types of script that can be run with Kirby : 
- `Scheduled`: Run at a frequency or a date given in the database (cron schedule expressions).
- `Daemon`: Jobs that need to be run in continuous.

.. note:: Cron schedule expressions example :

    :code:`5 4 * * *` = every day at 4:05
    :code:`*/2 * * * *` = every two minutes
    
    `This website <https://crontab.guru/>`_ can help you build cron schedule expressions

.. image:: _static/kirby-scripts.svg

The schema above shows an example of recommended structure for the scripts. 
The basic idea consists in separating the scripts in:
- *Sensors* (`Scheduled` script) that connect to external sources of data and send information into Topic(s).
- *Processors* (`Daemon` script) that process the data from Topic(s) and outputs them in an external, 
it can be another topic that will be read by other processors.

Multiple processors can connect to a Topic and be raised once a message is produced by the sensor.

The schedule is part of the metadata for the execution of the scripts. These are stored in the 
database.

## Database

.. image:: _static/kirby-model.svg

The image showed above is the export of the script database model.

The script to run is described in the `Script` table. The `package_name` represents the name of
the package that will be installed (with the correct `package_version`).

The script needs to be executed in a environment (`prod`, `dev`, `test` for instance).
If scheduled, the script needs a schedule link (otherwise this link wont be included).

In order to link a script that runs in various environments, we created a `job` table.

The context links all these tables together. It represents the execution context of 
the script.

`On failure` or `on retry` are notifications that will be sent.

.. todo:: The notification system is not implemented yet


## Web service

The web service expose the the database through a clear interface via an admin interface with an identification system. 
And an API used by kirby to access the database.

The next image shows a visualisation of the job table:

.. image:: _static/webapi/table.png

The next image shows the creation of a line in the job table:

.. image:: _static/webapi/database_edit.png

The following image is the log's screen:

.. image:: _static/webapi/logs.png

And finally, when connecting to the homepage of the web service you have acces to the list of the eng
.. image:: _static/webapi/api.png


## Supervisor & Scheduler

.. image:: _static/kirby-supervisor.svg

The user can raise as many `Supervisor` that he wants. One of the `Supervisor` is elected `Scheduler` via an election.

The latter is retrieving the schedule from the web service (see [Web Service](#id1)) and post the jobs 
in *Kafka Topics* : the topic `.kirby.job-offers.daemon` for daemons jobs  and the topic `.kirby.job-offers.scheduled` 
for scheduled tasks.



One `Runner` and one `Arbiter` are spawned per `Supervisor`.


## Runner & Arbiter

The scripts are run either by `Runner`s or `Arbiter`s depending on the *type* 
of the script: 
- `Runner` if the script is a `Scheduled`.
- `Arbiter` if it's a `Deamon`.

Their tasks are to retrieve the *jobs* posted on the Kafka topics (see [Supervisor & Scheduler](#supervisor--scheduler) 
for the topics concerned) 

:todo: explain Why kafka? How does it spread jobs... 
