import uuid
import os
from hotqueue import HotQueue
import redis


#redis_ip = os.environ.get('REDIS_IP')
#if not redis_ip:
#    raise Exception()

q = HotQueue("queue", host="127.0.0.1", port=6379, db=4)
rd_jobs = redis.Redis(host="127.0.0.1", port=6379, db=3)

def _generate_jid():
    """
    Generate a pseudo-random identifier for a job.
    """
    return str(uuid.uuid4())

def _generate_job_key(jid):
    """
    Generate the redis key from the job id to be used when storing, retrieving or updating
    a job in the database.
    """
    return 'job.{}'.format(jid)

def _instantiate_job(jid, status, upper, lower):
    """
    Create the job object description as a python dictionary. Requires the job id, status,
    start and end parameters.
    """
    if type(jid) == str:
        return {'id': jid,
                'status': status,
                'upper': upper,
                'lower': lower
                }
    return {'id': jid.decode('utf-8'),
            'status': status.decode('utf-8'),
            'upper': upper.decode('utf-8'),
            'lower': lower.decode('utf-8')
            }

def save_job(job_key, job_dict):
    """Save a job object in the Redis database."""
    rd_jobs.hset(job_key, mapping=job_dict)

def queue_job(jid):
    """Add a job to the redis queue."""
    q.put(jid)

def add_job(upper, lower, status="submitted"):
    """Add a job to the redis queue."""
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, upper, lower)
    _save_job(_generate_job_key(jid), job_dict)
    queue_job(jid)
    return job_dict

def update_job_status(jid, status):
    """Update the status of job with job id `jid` to status `status`."""
    job = rd_jobs.hgetall('job.{}'.format(jid))
    if job:
        job['status'] = status
        _save_job(_generate_job_key(jid), job)
    else:
        raise Exception()
