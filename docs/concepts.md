# Components

## Architecture

.. image:: _static/kirby-components.png


The scripts are run either by `Runner`s or `Arbiter`s depending on the *type* 
of the script: 
- `Runner` if the script is a `Scheduled`.
- `Arbiter` if it's a `Deamon`.

One `Runner` and one `Arbiter` are spawned per `Supervisor`, their tasks are to retrieve
the *jobs* planned in the database.

The user can raise as many `Supervisor` that he wants. 
One of the `Supervisor` is elected `Scheduler` (see [Supervisor](#id2) part).
The latter is retrieving the schedule from the web service 
(see [Web Service & Database](#id1) part) and post the jobs in a *Kafka Topic*.


## Web Service & Database 

.. image:: _static/kirby-model.png


## Supervisor

.. image:: _static/kirby-supervisor.png
