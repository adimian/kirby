# Comparison with other platforms

Kirby is still in active development, and aims to become a platform
for data processing. It draws its inspirations from many existing products. 
Some of them are listed here to help you evaluate whether Kirby is the right
choice for you. 

.. important:: Kirby developers are not specialists in the following products, 
               our opinion is expressed here in good faith but 
               could be inaccurate. Corrections and additions are welcome, 
               to come up with the most helpful vision for potential users.   

## Airflow

https://airflow.apache.org

Airflow is a Python framework for building workflows. 
It is a very mature and robust platform, has lot of plugins for various tasks, 
and before considering using Kirby, you should first evaluate Airflow. 

### Similarities

- Airflow allows you to define jobs and schedules
- You can define tasks dependencies / successors
- It shows job status (pending / success / failed)
- It allows replay / rewind (called "backfill")

### Differences

- Airflow is an execution framework, not a data-driven framework
- Scripts need to be manually copied on the server
- Metadata goes into a single database that can grow big fast
- Scripts only run in AirFlow, data storage has to happen outside of it
- DAGs are monoliths: you cannot tap into an existing flow, you either need to
  - coordinate and create your own DAG
  - modify the original DAG to add your own step
  
  
  
## Faust

https://github.com/robinhood/faust

Faust is used to build data-driven pipelines using `asyncio`, 
porting the notion of Kafka Streams to Python

### Similarities

- It has the concept of `Table` which is the inspiration for Kirby's `State`
- Supports deploying redundant workers and keeping them alive

### Differences

- Built upon `asyncio`, which does not fit well with CPU-bound tasks
- No support for scheduled tasks, monitoring, ...


## Streamparse

https://github.com/Parsely/streamparse

### Similarities

- Deploys packaged versions of your code on a cluster
- Supports data-driven tasks and scheduled tasks

### Differences

- Requires an Apache Storm cluster
- Data storage is handled outside of Storm


## Others

.. todo:: add more similar products
