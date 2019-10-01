from kirby.models.security import user_datastore
from kirby import models

BAKERY_API = "http://127.0.0.1:8000"
KAFKA_BOOTSTRAP_SERVERS = '127.0.0.1:9092'
KIRBY_WEB_SERVER = "http://127.0.0.1:8080"

dev_env = "dev"
test_env = "test"
prod_env = "prod"


ENVS = {dev_env: "Development"}

JOBS = {
    "sensorcash": {
        "description": "Fetch bakery realtime sales",
        "type": models.JobType.DAEMON,
        "package_version": {dev_env: "0.1"},
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "CASHREGISTER_TOPIC_NAME": "cashregister",
            "CASHREGISTER_ENDPOINT":"sales/cashregister"
        }
    },

    "realtime": {
        "description": "insert realtime",
        "type": models.JobType.SCHEDULED,
        "package_version": {dev_env: "0.1"},
        "scheduled_param": {
            "name": "every two minutes",
            "hour": "*",
            "minute": "*/2",
        },
        "config": {
            "BAKERY_API_BASE": BAKERY_API,
            "CASHREGISTER_TOPIC_NAME": "cashregister",
            "TOTAL_FILES_FOLDER_PATH":"/Users/nicksjl/realtime_totals/"
        },
    }}
EXT = ["bakery","cashregister","totalfiles"]



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
            config=info["config"],
        )
        for name, info in JOBS.items()
    }


def create_contexts(s, jobs, envs):
    def create_context(job, env_name, env):
        ctx = models.Context(job=job, environment=env)
        ctx.set_config(
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

    topic_names = EXT

    return {name: create_topic(name) for name in topic_names}


def create_scripts(s, contexts, jobs, envs):
    def create_script(name_job):
        for env_name, env in envs.items():
            job = jobs[name_job]
            package_version = JOBS[name_job]["package_version"][env_name]

            script = models.Script(
                context=contexts[(env, job)],
                package_name=name_job,
                package_version=package_version,
            )
            s.add(script)

    for job_name in JOBS.keys():
        create_script(job_name)


def create_short_demo_db(s):

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
