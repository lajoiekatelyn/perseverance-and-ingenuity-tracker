import json
from flask import Flask, request
import redis
import math

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
    return redis.Redis(host='127.0.0.1', port=6379, db=db_num, decode_responses=decode)

rd_rover = get_redis_client(0, True)
rd_heli = get_redis_client(1, True)
rd_img = get_redis_client(2, False)

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
            key = f'sol:{item["properties"]["sol"]}'
            item = json.dumps(item)            
            rd_rover.set(key, item)
        for item in helicopter_data['features']:
            key = f'sol:{item["properties"]["Sol"]}'
            item = json.dumps(item)
            rd_heli.set(key, item)
        return f'Data loaded into db.\n'
    elif request.method == 'DELETE':
        rd.flushdb()
        return f'Data deleted.\n'
    else:
        return 'The method you requested does not apply.\n', 400

@app.route('/rover/sols', methods=['GET'])
def get_rover_sols():
    """
    This function outputs all the sols during which the Mars rover was operational.
    Arguments
        None
    Returns
        sols_operational (list): integer numbers
    """
    return rd_rover.keys()

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

@app.route('/deployed/<string:sol>', methods=['GET'])
def get_deployed(sol:str):
    if rd_rover.get(sol) and rd_heli.get(sol):
        return f'Perseverance and Ingenuity were both deployed on {sol}.\n'
    elif rd_rover.get(sol):
        return f'Perseverance was deployed on {sol}, but Ingenuity was not.\n'
    elif rd_heli.get(sol):
        return f'Ingenuity was deployed on {sol}, but Perseverance was not.\n'
    else:
        return f'Neither Perseverance nor Ingeunity were deployed on {sol}.\n.' 

@app.route('/helicopter/sols', methods=['GET'])
def get_heli_sols():
    """
    This function outputs all the sols during which the Mars helicoper was operational.
    Arguments
        None
    Returns
        sols_operational (list): integer numbers
    """
    return rd_heli.keys()

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

"""@app.route('/rover/sols/<string:sol>/distance', methods=['GET'])
def get_dist_rover(sol:str) -> float:
    if not rd_rover.get(sol):
        return f'Perseverance was not deployed on {sol}.\n'
    else:
        data = json.loads(rd_rover.get(sol))
        coords = data['geometry']['coordinates']
        total_dist = 0
        for i in range(len(coords)-1):
            total_dist += calc_gcd(coords[i][1], coords[i][0], coords[i+1][1], coords[i+1][0], 3389.5)
        return {'distance_traveled_km': total_dist}

@app.route('/helicopter/sols/<string:sol>/distance', methods=['GET'])
def get_dist_heli(sol:str) -> float:
    if not rd_heli.get(sol):
        return f'Ingenuity was not deployed on {sol}.\n'
    else:
        data = json.loads(rd_heli.get(sol))
        coords = data['geometry']['coordinates']
        total_dist = 0
        for i in range(len(coords)-1):
            total_dist += calc_gcd(coords[i][1], coords[i][0], coords[i+1][1], coords[i+1][0], 3389.5)
        return {'distance_traveled_km': total_dist}
"""

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0')
