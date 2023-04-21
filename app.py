import json
from flask import Flask, request
import redis
import math
import matplotlib.pyplot as plt

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
    Returns sols_both_deployed (list): list of sols both rover and helicopter are deployed.
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

@app.route('/map', methods=['GET', 'POST', 'DELETE'])
def create_map():
    """
    """
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
    sol_bounds = {'lower_bound':200,'upper_bound':500}
    
    #converts from rd to sorted list
    for sol in rd_heli.keys():
        heli_sols.append(sol)
    heli_sols.sort()
    for sol in rd_rover.keys():
        rover_sols.append(sol)
    rover_sols.sort()

    if request.method == 'POST':
        counter = 0;
        for sol in heli_sols:
            sol_dict = json.loads(rd_heli.get(sol))
            if sol_dict["properties"]["Sol"] < sol_bounds['lower_bound']:
                continue;
            elif sol_dict["properties"]["Sol"] > sol_bounds['upper_bound']:
                continue;
            for point in sol_dict['geometry']['coordinates']:
                heli_x_pos.append(point[0])
                heli_y_pos.append(point[1])
                counter +=1
                if counter == len(sol_dict['geometry']['coordinates']):
                    heli_x_pos_end.append(point[0])
                    heli_y_pos_end.append(point[1])
                    counter = 0;
        for sol in rover_sols:
            #there seems to be an some corrdinates that are given as list
            sol_dict = json.loads(rd_rover.get(sol))
            if sol_dict["properties"]["sol"] < sol_bounds['lower_bound']:
                continue;
            elif sol_dict["properties"]["sol"] > sol_bounds['upper_bound']:
                continue;
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
        plt.savefig('./map.png')
        return rover_x_pos
    #returns to user
    elif request.method == 'GET':
        return 'a'
    elif request.method == 'DELETE':
        rd_image.flushdb()
        return 'Plot has been deleted from database'
    else:
        return 'a'


if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0')
