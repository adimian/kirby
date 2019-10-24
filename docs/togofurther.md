# To go further 
## Election process
Election process is explained in figure below. 

.. image:: _static/election_scheduler_diagram.png

Each `supervisor` creates a new thread (`timer` thread) 
 where it tries to become a leader every `LEADER_KEY_LEASE` seconds. 
 Default value is set to 0.5s.   
 To do so, a given `supervisor` (with for example `name=super`) read `KIRBY_LEADER`
 key from `redis` server. 
 If it is empty, or if `KIRBY_LEADER==super`, `supervisor` becomes or respectively 
 stays the leader
 and  set `KIRBY_LEADER` key to `super` for a 7.5s duration.
 It means that when a `supervisor` is leader, it stays the leader until it crashes. 
 Maximum 7.5s later after leader crash, another `supervisor` takes the lead. 
 
 
 ##Scheduler process
 Scheduler process is explained in figure above.
 
 Scripts information (among others package name and schedule) is stored in 
 the scripts database.
 `kirby` Web API `/schedule` endpoint returns a list of scripts that must be run 
 (following their schedule).
 
 When starting a `supervisor`, a `scheduler` instance is created. 
 If `supervisor` is the leader, every `WAKEUP` seconds (default = 30s) its
 `scheduler`  will fetch jobs from `kirby` script database using `/schedule` 
  `kirby` web endpoint
 and send them to the appropriate  `Kafka` `job-offers` topic (daemon or scheduled).
 
 
 
 #Arbiter/Runner process
`arbiter` and `runner` processes are explained in figure below for one given `supervisor`.

.. image:: _static/runner_arbiter_diagram.png

 Concerning those processes, all `supervisors` (leader and others) behave exactly the same way. 
 Once run, a `supervisor` creates : 
 - a `runner` instance in a new thread to deal with scheduled scripts,
 - an `arbiter` (also in a new thread) to deal with daemon scripts. 
 
`arbiter` and `runner` are consuming jobs respectively from `.kirby.job-offers.daemon`
 kafka topic and 
`.kirby.job-offers.scheduled` kafka topic. As a reminder, those topics are fed by the 
`scheduler` of the leader `supervisor`. 
Once a job is fetched, an `executor` instance is created in a new thread. This `executor`
creates a Python virtual environment in `.kirby.virtualenv` folder and installs (trough `pypi`)
user's script and all associated dependencies (including `irby`)  
`executor` then runs the script in a subprocess. This script creates a `kirby` instance. 
After what it registers its externals (source and destination). When doing that, 
`kirby` checks that externals given in user's script exist in the script database. If 
not, an exception is returned. 
User's script should also contain `logger.log` that send messages on `_logs` kafka topic. 
The latest is consumed by `kirby` web API to print logs in `logs` tab. 
Once user's script is over, associated subprocess and thread are closed.
The two only behaviour difference between `arbiter` and `runner` are the following :
- when a daemon script fails, the `arbiter` try to re-run it, 
- `arbiters` of all `supervisors` have a different `group id` which mean that they all run
every single daemon script. Scheduled scripts are only run once. 

 
.. image:: _static/runner_arbiter_diagram.png

 

 
   
