import json
from flask import Flask, request, send_file
import redis
import math
import matplotlib.pyplot as plt
import requests
import os
import jobs

app = Flask(__name__)

rover_data = {}
helicopter_data = {}

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

def calc_gcd(latitude_1: float, longitude_1: float, latitude_2: float, longitude_2: float, radius:float) -> float:
    """
    This function was written by Joe Wallen. Modifies to remove global variables and make it applicable to a planent
    of any radius.
    Arguments:
        latitude_1 (float): latitude at which the robot starts its journey.
        latitude_2 (float): latitude at which the robot ends its journey.
        longitude_1 (float): longitude at which the robot starts its journey.
        longitude_2 (float): longitude at which the robot ends its journey.
        radius (float): the radius of the planet the robot is traversing.
    Returns:
        distance (float): the distance that a robot has to travel to get between two (lat, long) points.
    """

    lat1, lon1, lat2, lon2 = map( math.radians, [latitude_1, longitude_1, latitude_2, longitude_2] )
    d_sigma = math.acos( math.sin(lat1) * math.sin(lat2) + math.cos(lat1) * math.cos(lat2) * math.cos(abs(lon1-lon2)))
    return ( radius * d_sigma )

@app.route('/data', methods=['GET', 'POST', 'DELETE'])
def get_route():
    """
    This function either posts, outputs, or deletes all data in the Redis database.
    Arguments
        None
    Returns
        None
    """
    if request.method == 'GET':
        output_list = ['ROVER DATA']
        for item in rd_rover.keys():
            output_list.append(json.loads(rd_rover.get(item)))
        output_list.append('HELICOPTER DATA')
        for item in rd_heli.keys():
            output_list.append(json.loads(rd_heli.get(item)))
        return output_list
    
    elif request.method == 'POST':
        with open('rover_drive_path.json', 'r') as f:
            rover_data = json.load(f)
        with open('helicopter_flight_path.json', 'r') as f:
            helicopter_data = json.load(f)
            
        for item in rover_data['features']:
            if int(item['properties']['sol']) < 10:
                key = f'sol:000{item["properties"]["sol"]}'
                item = json.dumps(item)            
                rd_rover.set(key, item)
            elif int(item["properties"]["sol"])>=10 and int(item["properties"]["sol"])<100:
                key = f'sol:00{item["properties"]["sol"]}'
                item = json.dumps(item)
                rd_rover.set(key, item)
            elif int(item["properties"]["sol"])>=100 and int(item["properties"]["sol"])<1000:
                key = f'sol:0{item["properties"]["sol"]}'
                item = json.dumps(item)
                rd_rover.set(key, item)
            else:
                key = f'sol:{item["properties"]["sol"]}'
                item = json.dumps(item)
                rd_rover.set(key, item)
            
        for item in helicopter_data['features']:
            if int(item["properties"]["Sol"])<10:
                key = f'sol:000{item["properties"]["Sol"]}'
                item = json.dumps(item)
                rd_heli.set(key, item)
            elif int(item["properties"]["Sol"])>=10 and int(item["properties"]["Sol"])<100:
                key = f'sol:00{item["properties"]["Sol"]}'
                item = json.dumps(item)
                rd_heli.set(key, item)
            elif int(item["properties"]["Sol"])>=100 and int(item["properties"]["Sol"])<1000:
                key = f'sol:0{item["properties"]["Sol"]}'
                item = json.dumps(item)
                rd_heli.set(key, item)
            else:
                key = f'sol:{item["properties"]["Sol"]}'
                item = json.dumps(item)
                rd_heli.set(key, item)
        return f'Data loaded into db.\n'
    elif request.method == 'DELETE':
        rd_rover.flushdb()
        rd_heli.flushdb()
        return f'Data deleted.\n'
    else:
        return 'The method you requested does not apply.\n', 400

@app.route('/rover')
def get_rover_data():
    """
    This function returns rover path data
    Arguments
        None
    Returns
        output_list (list): all of the rover path data
    """
    output_list = ['ROVER DATA']
    for item in rd_rover.keys():
        output_list.append(json.loads(rd_rover.get(item)))
    return output_list
@app.route('/helicopter')
def get_heli_data():
    """
     This function returns helicopter path data
    Arguments
        None
    Returns
        output_list (list): all of the helicopter path data
    """
    output_list = ['HELICOPTER DATA']
    for item in rd_heli.keys():
        output_list.append(json.loads(rd_heli.get(item)))
    return output_list
    

@app.route('/rover/sols', methods=['GET'])
def get_rover_sols():
    """
    This function outputs all the sols during which the Mars rover was operational.
    Arguments
        None
    Returns
        sols_operational (list): integer numbers
    """
    sols = []
    for sol in rd_rover.keys():
        sols.append(sol)
    sols.sort()
    return sols

@app.route('/rover/sols/<string:sol>', methods=['GET'])
def get_rover_sol(sol:str):
    """
    This function retrieves a specific sol from the rover database.
    Arguments
        sol (str): string of sol:<int>, ex sol:401 
    Returns
        sol_info (dict): all information avaliable for sol of concern
    """
    if rd_rover.get(sol) == None:
        return f'{sol} is not a sol in the rover dataset. Please try another.\n', 400

    ret = json.loads(rd_rover.get(sol))
    return ret

@app.route('/both_deployed', methods=['GET'])
def get_deployed() -> list:
    """
    This function returns all the sols during which both the rover and the helicopter were deployed.
    Arguments
        None
    Returns 
        sols_both_deployed (list): list of sols where both rover and helicopter are deployed.
    """
    both = []
    keys = rd_heli.keys()
    for sol in keys:
        if rd_rover.get(sol):
            both.append(sol)
    return both 

@app.route('/helicopter/sols', methods=['GET'])
def get_heli_sols():
    """
    This function outputs all the sols during which the Mars helicoper was operational.
    Arguments
        None
    Returns
        sols_operational (list): integer numbers
    """
    sols = []
    for sol in rd_heli.keys():
        sols.append(sol)
    sols.sort()
    return sols

@app.route('/helicopter/sols/<string:sol>', methods=['GET'])
def get_heli_sol(sol:str):
    """
    This function retrieves a specific sol from the rover database.
    Arguments
        sol (str): string of sol:<int>, ex sol:401
    Returns
        sol_info (dict): all information avaliable for sol of concern
    """
    if rd_heli.get(sol) == None:
        return f'{sol} is not a sol in the helicopter dataset. Please try another.\n', 400

    ret = json.loads(rd_heli.get(sol))
    return ret

@app.route('/rover/sols/<string:sol>/helicopter', methods=['GET'])
def shortest_dist_between_agents(sol:str):
    """
    This function returns list of all flights.
    Arguments
        sol (str): sol of interest
    Returns
        shortest_dist (dictionary): shortest distance between the two robots on a given sol
    """
    if rd_heli.get(sol) and rd_rover.get(sol):
        shortest_dist = float('inf')
        rover_data = json.loads(rd_rover.get(sol))
        rover_coords = rover_data['geometry']['coordinates']
        heli_data = json.loads(rd_heli.get(sol))
        heli_coords = heli_data['geometry']['coordinates']
        for i in range(len(rover_coords)):
            for j in range(len(heli_coords)):
                dist = calc_gcd(rover_coords[i][1], rover_coords[i][0], heli_coords[j][1], heli_coords[j][0], 3389.5) * 1000
                if (dist < shortest_dist):
                    shortest_dist = dist
        return {'shortest_dist': shortest_dist}
    else:
        return f'Either Perseverance or Ingenuity was not deployed on {sol}.\n', 400


@app.route('/helicopter/flights', methods=['GET'])
def get_heli_flights():
    """
    This function returns list of all flights. 
    Arguments
        None
    Returns
        flights (list): list of all flights in dataset 
    """    
    flights = []
    for sol in rd_heli.keys():
        sol_dict = json.loads(rd_heli.get(sol))
        flight_num = sol_dict['properties']['Flight']
        flights.append(f"Flight:{flight_num}")
    return flights

@app.route('/helicopter/flights/<string:flight>', methods=['GET'])
def get_heli_flight(flight:str):
    """
    This function returns information regarding specified flight.
    Arguments
        flight (str): flight of interest
    Returns
        sol_dict (dictionary): data related to the flight specified
    """
    flight = flight[7:]
    for sol in rd_heli.keys():
        sol_dict = json.loads(rd_heli.get(sol))
        flight_num = sol_dict['properties']['Flight']
        if str(flight) == str(flight_num):
            return sol_dict

    return f"The data for flight:{flight} is not within the dataset.\n",400

@app.route('/map/<string:jid>', methods=['GET', 'DELETE'])
def create_map(jid:str):
    """
    This function either gets, post, or deletes map of rover and helicopter's paths
    Arguments
        jid (str): job identifier
    Returns
    """
    #jid = 'job.{}'.format(jid)
    if request.method == 'GET':
        if rd_img.exists(jid):
            return json.loads(rd_img.get(jid))
        else:
            return "Map for specified job does not exist"
    elif request.method == 'DELETE':
        data = json.loads(rd_img.get(jid))
        delete_hash = data['data']["deletehash"]
        url = f'https://api.imgur.com/3/image/{delete_hash}'
        headers = {'Authorization': 'Client-ID cf0aaf4466732fb'}
        response = requests.delete(url, headers=headers)
        rd_img.flushdb()
        return 'Plot has been deleted from redis and imgur.\n'
    else:
        return 'The method you requested is not an option.\n'


@app.route('/help', methods=['GET'])
def help():
     message = "usage: curl localhost:5000[Options]\n\n  *** Note that for routes with POST or DELETE in their descriptions -X POST or -X DELETE will need \
to be added to the curl command \n    Options: \n       [/data]                                 GET POST OR DELETE entire data set \n       [/rover]       \
                         Return list of path data set \n       [/helicopter]                           Return list of all path data \n       [/rover/sols] \
                          Return list of sols in rover data\n       [/rover/sols/<string:sol>]              Return data for specific sol\n       [/both_dep\
loyed]                        Return sols where both are deployed \n       [/helicopter/sols]                      Returns list of sols in data \n       [/\
helicopter/sols/<string:sol>]         Return data for a given sol \n       [/rover/sols/<string:sol>/helicopter]   Returns shortest distance for a given so\
l \n       [/helicopter/flights]                   Return list of flights in data \n       [/helicopter/flights/<string:flight>]   Return data for a given \
flight \n       [/map]                                  GET or DELETE plot with path data \n       [/jobs]                                 Create a plot/jo\
b \n       [/help]                                 Return string with information on routes"
     return message


@app.route('/jobs', methods=['GET', 'POST', 'DELETE'])
def jobs_api():
    """
    API route for creating a new job to do some analysis. This route accepts a JSON payload
    describing the job to be created.
    """
    if request.method == 'GET':
        try:
            job = request.get_json(force=True)
        except Exception as e:
            return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})
        if rd_img.get(job['id']):
            return json.dumps(rd_img.get(job['id']))
        else:
            return 'Image not in database. Please query an image request, or check back later.', 400
    elif request.method == 'POST':
        try:
            job = request.get_json(force=True)
        except Exception as e:
            return json.dumps({'status': "Error", 'message': 'Invalid JSON: {}.'.format(e)})
        job = jobs.add_job(job['upper'], job['lower'])
        return 'Job submitted. Please wait a moment to check jid: {} for completion.\n'.format(job['id'])
    elif request.method == 'DELETE':
        rd_img.flushdb()
    else:
        return 'Method requested not applicable. Please try again.\n', 400

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0')
