# Components

.. image:: _static/kirby-components.png

Above is the diagram of all components of Kirby along with the dataflow and interprocess calls. Each and every one of
the components are described in the following.

It is highly recommended to understand how [Kafka](https://kafka.apache.org/) works in order to comprehend the components
of Kirby.

## Scripts

Kirby's task is to handle the execution of scripts that process data. 
The data which come from externals sources of Kirby can move between processes via Kafka topics. 

Currently as external sources, Kirby proposes support for `Web Services`,  `Topics` and `Files`.

The Kafka topics used by the Kirby object `Topic` are stored alongside the needed topics for Kirby.

There is two types of script that can be run with Kirby : 
- `Scheduled`: Run at a frequency or a date given in the database (cron schedule expressions).
- `Deamon`: Jobs that need to be run in continuous.

.. note:: Cron schedule expressions example :

    :code:`5 4 * * *` = every day at 4:05
    :code:`*/2 * * * *` = every two minutes
    
    `This website <https://crontab.guru/>`_ can help you build cron schedule expressions

.. image:: _static/kirby-scripts.png

The schema above shows an example of recommended structure for the scripts. The basic idea consists in separating the 
scripts in:
- *Sensors* (`Scheduled` script) that connects to external source of data and send them into Topic(s).
- *Processor* (`Deamon` script) that processes the data from Topic(s) and outputs them in an external, 
it can be another topic that will be read by other processors.

Multiple processors can connect to a Topic and be raised once a message is produced by the sensor.

The schedule is part of the metadata for the execution of the scripts. These are stored in the 
database.

## Database

.. image:: _static/kirby-model.png

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


.. todo: schedule endpoint


## Supervisor & Scheduler

.. image:: _static/kirby-supervisor.png

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
