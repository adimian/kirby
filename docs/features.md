# Features

## For Infrastructure/Ops

### De-centralized worker deployment

- Scripts are deployed from the web UI
- Versioned, can co-exist in many versions at once
- If you can publish to PyPi, it can be deployed

### Real-time monitoring

- Jobs send their status (success / fail) and logs in real time
- Notifications can be configured per job to be triggered in case of failure or missed mark (should be running but is not)

### Centralized secrets management

- Scripts pull their configuration from the "vault"
- Secrets are stored in a central place
- Secrets are never persisted on disk
- ACL apply to secret access

### Multiple authentication backends (local, ldap, ...)

- Authentication
  - LDAP
  - Okta
  - Local accounts

- Authorization
  - Groups 
  - Roles

## For Developers

### Workers as simple python scripts

- Scripts are simple Python scripts
- You can use whatever library you want, as long as it can be pip-installed
- No hard requirement on using Kirby at all
- Configuration is passed through env variables

### File-based local unit-testing

- Kirby is meant to be testable
- All input / output in Kirby is a message
- Messages are simulated using folders and files
- Comes with integrated testing helpers

### Simple integration to web frameworks

- Designed to allow swap-in replacement of Celery
  - ex: produce data in an ETL script, use it straight in your app, or the other way around
- Chord / group logic is replaced by stream piping
- Higher throughput and parallelism
- Simpler status management and failure recovery
- Not limited to running jobs, integrations can also serve as a view on all Kirby-managed data
- Can be used in templates, views, etc.


## For Data Engineers

### Scheduled tasks with exceptions 

- Schedule can be configured with cron-like syntax
- Add exceptions to pause or slow down a job from running (when source is broken for instance)
- Automatically back to normal schedule at the end of the exception, no need to undo them


### Rewind/replay of tasks

- Rewind a data source and all downstream processing will flow naturally (but will flag the data as the result of a re-run in case it matters)
- Replay production data in preprod or even on a developer laptop → testing with prod data = easier development / debugging


### Data traceability with data dependency graph documentation 

- Each process adds itself in the message headers, to allow end-to-end data traceability
- Visualize data flows in the web UI to understand 
  - where your data comes from
  - when it was processed
  - what transformations were applied

### Computed tables

- Kirby **State** objects allows you to keep a persistent object that can be updated by scripts
- By default, a state only shows its latest version, but each mutation is versioned and can be recovered (only limited by disk space)
- Useful for "hot" data with expensive computation costs
