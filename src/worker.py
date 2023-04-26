from jobs import q, update_job_status
import redis

def get_redis_client(db_num:int, decode:bool):
    """
    This function creates a connection to a Redis database

    Arguments
        None
    Returns
        redis_database (redis.client.Redis): Redis client
    """

    redis_ip = os.environ.get('REDIS_IP')
    if not redis_ip:
        raise Exception()

    return redis.Redis(host=redis_ip, port=6379, db=db_num, decode_responses=decode)

rd_rover = get_redis_client(0, True)
rd_heli = get_redis_client(1, True)
rd_img = get_redis_client(2, True)
rd_jobs = get_redis_client(3, True)

#how are we getting redis data
#how are we getting jid
#how are we 

@q.worker
def execute_job(jid):
    """
    Retrieve a job id from the task queue and execute the job.
    Monitors the job to completion and updates the database accordingly.

    Arguments 
        jid (string): job identifier
    Return 
        None
    """
    jobs.update_job_status(jid, 'in progress')

    job_dict = rd_jobs.hgetall(jid)
    
    if len(rd_heli.keys()) == 0:
        return 'There is no data in the database; image cannot be created.\n', 400
        
        heli_x_pos =[]
        heli_y_pos = []
        rover_x_pos = []
        rover_y_pos = []
        
        heli_x_pos_end =[]
        heli_y_pos_end = []
        rover_x_pos_end = []
        rover_y_pos_end = []
        
        heli_sols = []
        rover_sols = []
        lower = job_dict['lower']
        upper = job_dict['upper']

        if lower:
            try:
                lower = int(lower)
            except ValueError:
                return "Invalid lower bound parameter; must be an integer.\n"
        if upper:
            try:
                upper = int(upper)
            except ValueError:
                return "Invalid upper bound parameter; must be an integer.\n"

        lower = int(lower)
        upper = int(upper)

        if lower >= upper:
            return "[ERROR] Upper bound must be larger than lower bound"
        
        sol_bounds = {'lower':lower,'upper':upper}
        
        #converts from rd to sorted list
        for sol in rd_heli.keys():
            heli_sols.append(sol)
            heli_sols.sort()
        for sol in rd_rover.keys():
            rover_sols.append(sol)
            rover_sols.sort()

        counter = 0;
        for sol in heli_sols:
            sol_dict = json.loads(rd_heli.get(sol))
            if sol_dict["properties"]["Sol"] > sol_bounds['lower'] and sol_dict["properties"]["Sol"] < sol_bounds['upper']:
                for point in sol_dict['geometry']['coordinates']:
                    heli_x_pos.append(point[0])
                    heli_y_pos.append(point[1])
                    counter +=1
                    if counter == len(sol_dict['geometry']['coordinates']):
                        heli_x_pos_end.append(point[0])
                        heli_y_pos_end.append(point[1])
                        counter = 0;
        for sol in rover_sols:
            sol_dict = json.loads(rd_rover.get(sol))
            if sol_dict["properties"]["sol"] > sol_bounds['lower'] and sol_dict["properties"]["sol"] < sol_bounds['upper']:
                if sol_dict['geometry']['type'] == 'MultiLineString':
                    counter2 = 0
                    for lists_of_coords in sol_dict['geometry']['coordinates']:
                        counter +=1
                        for point in lists_of_coords:
                            rover_x_pos.append(point[0])
                            rover_y_pos.append(point[1])
                            counter2+=1
                            if counter == len(sol_dict['geometry']['coordinates']) and counter2 == len(lists_of_coords):
                                rover_x_pos_end.append(point[0])
                                rover_y_pos_end.append(point[1])
                                counter=0
                                counter2=0
                        
                elif sol_dict['geometry']['type'] == 'LineString':
                    for point in sol_dict['geometry']['coordinates']:
                        rover_x_pos.append(point[0])
                        rover_y_pos.append(point[1])
                        counter+=1
                        if counter == len(sol_dict['geometry']['coordinates']):
                            rover_x_pos_end.append(point[0])
                            rover_y_pos_end.append(point[1])
                            counter=0
        
        plt.plot(heli_x_pos,heli_y_pos,label='Ingenuity')
        plt.plot(rover_x_pos,rover_y_pos,label='Perseverance')
        plt.scatter(heli_x_pos_end,heli_y_pos_end)
        plt.scatter(rover_x_pos_end,rover_y_pos_end)
        plt.title('Map of Ingenuity and Perseverance Path')
        plt.grid(True, color='gray', linestyle='--')
        plt.xlabel("Latitude ($^{\circ}$)")
        plt.ylabel("Longitude ($^{\circ}$)")
        plt.legend()
        plt.savefig('map.png')
        headers = {'Authorization': 'Bearer 5eeae49394cd929e299785c8805bd168fc675280'}
        data = {'image': open('./map.png', 'rb')}
        response = requests.post(url="https://api.imgur.com/3/upload", headers=headers, files=data)
        rd_img.set(jid, response.content)
    #returns to user


    jobs.update_job_status(jid, 'complete')

if __name__ == '__main__':
    jid = q.get()
    execute_job(jid)
