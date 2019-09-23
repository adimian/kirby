from kirby.models.security import user_datastore
from kirby import models

dev_env = "dev"
test_env = "test"
prod_env = "prod"

package_version = {dev_env: "1.0.5", test_env: "0.0.5", prod_env: "2.0.5"}
config_context = {
    dev_env: {"BAKERY_API_BASE": "http://some.server.somewhere:8000"},
    test_env: {"BAKERY_API_BASE": "localhost:8000"},
    prod_env: {"BAKERY_API_BASE": "http://some.server.elsewhere:8000"},
}

ENVS = {dev_env: "Development", test_env: "Test", prod_env: "Production"}

ENV_VARS = {
    models.ConfigScope.GLOBAL: {
        "KAFKA_BOOTSTRAP_SERVERS": "localhost:9092",
        "KIRBY_WEB_SERVER": "localhost:8080",
    }
}

TOPICS = {"bakery", "cashregister", "orders", "timeseries", "factory"}

JOBS = {
    "sensor_cashregister": {
        "description": "Fetch bakery realtime sales",
        "type": models.JobType.DAEMON,
        "package_version": package_version,
        "config": {
            models.ConfigScope.JOB: {
                "CASHREGISTER_TOPIC_NAME": "cashregister"
            },
            models.ConfigScope.CONTEXT: config_context,
        },
    },
    "sensor_orders": {
        "description": "Fetch bakery forecast sales",
        "type": models.JobType.SCHEDULED,
        "package_version": package_version,
        "scheduled_param": {
            "name": "every two minutes",
            "hour": "*",
            "minute": "*/2",
        },
        "config": {
            models.ConfigScope.JOB: {"ORDERS_TOPIC_NAME": "orders"},
            models.ConfigScope.CONTEXT: config_context,
        },
    },
    "insert_forecast": {
        "description": "From forecast, push points on the timeseries tables",
        "type": models.JobType.DAEMON,
        "package_version": package_version,
        "config": {
            models.ConfigScope.JOB: {
                "CASHREGISTER_TOPIC_NAME": "cashregister"
            },
            models.ConfigScope.CONTEXT: config_context,
        },
    },
    "insert_realtime": {
        "description": "From realtime, push points on the timeseries tables",
        "type": models.JobType.DAEMON,
        "package_version": package_version,
        "config": {
            models.ConfigScope.JOB: {"ORDERS_TOPIC_NAME": "orders"},
            models.ConfigScope.CONTEXT: config_context,
        },
    },
    "booking_process": {
        "description": "From forecast send orders to the factory",
        "type": models.JobType.SCHEDULED,
        "package_version": package_version,
        "scheduled_param": {"name": "every day at 6am", "hour": "6"},
        "config": {
            models.ConfigScope.JOB: {"ORDERS_TOPIC_NAME": "orders"},
            models.ConfigScope.CONTEXT: config_context,
        },
    },
}


def create_envs(s):
    def create_env(name):
        env = models.Environment(name=name)
        s.add(env)
        return env

    return {short_name: create_env(name) for short_name, name in ENVS.items()}


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
            config=info["config"][models.ConfigScope.JOB],
        )
        for name, info in JOBS.items()
    }


def create_contexts(s, jobs, envs):
    def create_context(job_name, job, env_name, env):
        ctx = models.Context(job=job, environment=env)
        ctx.set_config(
            **JOBS[job_name]["config"][models.ConfigScope.CONTEXT][env_name]
        )
        s.add(ctx)
        return ctx

    return {
        (env, job): create_context(job_name, job, env_name, env)
        for env_name, env in envs.items()
        for job_name, job in jobs.items()
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


def create_config_keys(s):
    # Global vars
    scope = models.ConfigScope.GLOBAL
    for k, v in ENV_VARS[scope].items():
        s.add(models.ConfigKey(name=k, value=v, scope=scope))


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

    create_config_keys(s)

    s.commit()
