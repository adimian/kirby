from kirby.models.security import user_datastore
from kirby import models

BAKERY_API = "http://some.server.somewhere"
KAFKA_BOOTSTRAP_SERVERS = "some.kafka.server:9999"
KIRBY_WEB_SERVER = "some.kirby.server:9090"

ENVS = {
    "Development": ("dev", "1.0.5"),
    "Test": ("test", "0.0.5"),
    "Production": ("prod", "2.0.5"),
}
TOPICS = {"bakery", "cashregister", "orders", "timeseries", "factory"}
JOBS = {
    "sensor_cashregister": {
        "description": "Fetch bakery realtime sales",
        "type": models.JobType.DAEMON,
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "CASHREGISTER_TOPIC_NAME": "cashregister",
        },
    },
    "sensor_orders": {
        "description": "Fetch bakery forecast sales",
        "type": models.JobType.SCHEDULED,
        "scheduled_param": {
            "name": "every two minutes",
            "hour": "*",
            "minute": "*/2",
        },
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "ORDERS_TOPIC_NAME": "orders",
        },
    },
    "insert_forecast": {
        "description": "From forecast, push points on the timeseries tables",
        "type": models.JobType.DAEMON,
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "CASHREGISTER_TOPIC_NAME": "cashregister",
        },
    },
    "insert_realtime": {
        "description": "From realtime, push points on the timeseries tables",
        "type": models.JobType.DAEMON,
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "ORDERS_TOPIC_NAME": "orders",
        },
    },
    "booking_process": {
        "description": "From forecast send orders to the factory",
        "type": models.JobType.SCHEDULED,
        "scheduled_param": {"name": "every day at 6am", "hour": "6"},
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "ORDERS_TOPIC_NAME": "orders",
        },
    },
}


def create_envs(s):
    def create_env(name):
        env = models.Environment(name=name)
        s.add(env)
        return env

    return {
        short_name: create_env(name) for short_name, (name, _) in ENVS.items()
    }


def create_jobs(s, sysadmins):
    def create_job(description, type, config):
        job = models.Job(name=description, type=type)
        job.set_config(**config)
        job.add_notification(sysadmins, on_failure=True, on_retry=False)
        s.add(job)
        return job

    return {
        name: create_job(
            description=info["description"],
            type=info["type"],
            config=info["config"],
        )
        for name, info in JOBS.items()
    }


def create_contexts(s, jobs, envs):
    def create_context(job, env_name, env):
        ctx = models.Context(job=job, environment=env)
        ctx.set_config(
            ID=job.id,
            ENV=env_name,
            KIRBY_WEB_SERVER=KIRBY_WEB_SERVER,
            KAFKA_BOOTSTRAP_SERVERS=KAFKA_BOOTSTRAP_SERVERS,
        )
        s.add(ctx)
        return ctx

    return {
        (env, job): create_context(job, env_name, env)
        for env_name, env in envs.items()
        for job in jobs.values()
    }


def add_schedules(s, envs, jobs, contexts):
    def add_schedule_to_contexts(job_name, schedule):
        s.add(schedule)
        for env in envs.values():
            contexts[(env, jobs[job_name])].add_schedule(schedule)

    for job_name, job_info in JOBS.items():
        if job_info["type"] == models.JobType.SCHEDULED:
            add_schedule_to_contexts(
                job_name, models.Schedule(**job_info["scheduled_param"])
            )


def create_topics(s):
    def create_topic(name):
        topic = models.Topic(name=name)
        s.add(topic)
        return topic

    return {topic_name: create_topic(topic_name) for topic_name in TOPICS}


def create_scripts(s, contexts, jobs, envs):
    def create_script(name_job):
        for env_name, env in envs.items():
            job = jobs[name_job]
            package_version = ENVS[env_name][1]

            script = models.Script(
                context=contexts[(env, job)],
                package_name=f"{name_job}_for_{env_name}",
                package_version=package_version,
            )
            s.add(script)

    for job_name in JOBS.keys():
        create_script(job_name)


def create_demo_db(s):

    # create demo user
    user = user_datastore.create_user(username="demo", password="demo")
    role = user_datastore.find_role("admin")
    user_datastore.add_role_to_user(user=user, role=role)
    s.commit()

    sysadmins = models.NotificationGroup(name="sysadmins")
    sysadmins.add_email("alice@local.local")
    sysadmins.add_email("bob@local.local")
    sysadmins.add_email("charles@local.local")

    s.add(sysadmins)
    s.commit()

    # fill the database with dummy content
    jobs = create_jobs(s, sysadmins)

    envs = create_envs(s)

    contexts = create_contexts(s, jobs, envs)

    add_schedules(s, envs, jobs, contexts)

    create_topics(s)

    create_scripts(s, contexts, jobs, envs)

    s.commit()
