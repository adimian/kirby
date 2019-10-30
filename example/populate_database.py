import json
from kirby import models
from kirby.models import NotificationGroup
from kirby.models.security import user_datastore


def create_config_keys(s, env_var_dict):
    # Global vars
    scope = models.ConfigScope.GLOBAL
    for k, v in env_var_dict[scope].items():
        s.add(models.ConfigKey(name=k, value=v, scope=scope))


def create_envs(s, env_dict):
    def create_env(name):
        env = models.Environment(name=name)
        s.add(env)
        return env

    return {
        short_name: create_env(name) for short_name, name in env_dict.items()
    }


def create_jobs(s, job_dict):
    def create_job(description, type, notification_group, config):
        job = models.Job(name=description, type=type)
        job.set_config(**config)
        notification_group_db = s.query(NotificationGroup).filter_by(
            name=notification_group
        )[0]
        job.add_notification(
            notification_group_db, on_failure=True, on_retry=False
        )
        s.add(job)
        return job

    return {
        name: create_job(
            description=info["description"],
            type=info["type"],
            notification_group=info["notification_group"],
            config=info["config"][models.ConfigScope.JOB],
        )
        for name, info in job_dict.items()
    }


def create_contexts(s, jobs, envs, job_dict):
    def create_context(job_name, job, env_name, env):
        ctx = models.Context(job=job, environment=env)
        ctx.set_config(
            **job_dict[job_name]["config"][models.ConfigScope.CONTEXT][
                env_name
            ]
        )
        s.add(ctx)
        return ctx

    return {
        (env, job): create_context(job_name, job, env_name, env)
        for env_name, env in envs.items()
        for job_name, job in jobs.items()
    }


def add_schedules(s, envs, jobs, contexts, job_dict):
    def add_schedule_to_contexts(job_name, schedule):
        s.add(schedule)
        for env in envs.values():
            contexts[(env, jobs[job_name])].add_schedule(schedule)

    for job_name, job_info in job_dict.items():
        if job_info["type"] == models.JobType.SCHEDULED:
            add_schedule_to_contexts(
                job_name, models.Schedule(**job_info["scheduled_param"])
            )


def create_exts(s, ext_dict):
    def create_ext(name):
        topic = models.Topic(name=name)
        s.add(topic)
        return topic

    return {name: create_ext(name) for name in ext_dict}


def create_scripts(s, contexts, jobs, envs, job_dict):
    def create_script(name_job):
        for env_name, env in envs.items():
            job = jobs[name_job]
            package_version = job_dict[name_job]["package_version"][env_name]

            script = models.Script(
                context=contexts[(env, job)],
                package_name=name_job,
                package_version=package_version,
            )
            s.add(script)

    for job_name in job_dict.keys():
        create_script(job_name)


def read_json(demo_json_file_path):
    with open(demo_json_file_path, "r") as f:
        json_content = json.load(f)
    env_dict = json_content["ENVS"]
    env_var_dict = json_content["ENV_VARS"]
    job_dict = json_content["JOBS"]
    ext_list = json_content["EXTS"]
    user_list = json_content["USERS"]
    notification_group_dict = json_content["NOTIFICATION_GROUPS"]

    for key, value in job_dict.items():
        if value["type"] == "daemon":
            value["type"] = models.JobType.DAEMON
        elif value["type"] == "scheduled":
            value["type"] = models.JobType.SCHEDULED
        else:
            raise Exception(
                f"type {value['type']} not accepted in job type. Use only daemon or scheduled"
            )
        value["config"][models.ConfigScope.JOB] = value["config"].pop("JOB")
        value["config"][models.ConfigScope.CONTEXT] = value["config"].pop(
            "CONTEXT"
        )
    env_var_dict[models.ConfigScope.GLOBAL] = env_var_dict.pop("GLOBAL")
    return (
        env_dict,
        env_var_dict,
        job_dict,
        ext_list,
        user_list,
        notification_group_dict,
    )


def create_example_db(s, demo_json_file_path):
    env_dict, env_var_dict, job_dict, ext_dict, user_list, notification_group_dict = read_json(
        demo_json_file_path
    )

    # create demo user
    for user in user_list:
        user_db = user_datastore.create_user(
            username=user["username"], password=user["password"]
        )
        role_db = user_datastore.find_role(user["role"])
        user_datastore.add_role_to_user(user=user_db, role=role_db)
        s.commit()

    # create notification groups
    for name, mails in notification_group_dict.items():
        group = models.NotificationGroup(name=name)
        for mail in mails:
            group.add_email(mail)
        s.add(group)

        s.commit()

    # fill the database with dummy content
    jobs = create_jobs(s, job_dict)

    envs = create_envs(s, env_dict)

    contexts = create_contexts(s, jobs, envs, job_dict)

    add_schedules(s, envs, jobs, contexts, job_dict)

    create_exts(s, ext_dict)

    create_scripts(s, contexts, jobs, envs, job_dict)

    create_config_keys(s, env_var_dict)

    s.commit()
