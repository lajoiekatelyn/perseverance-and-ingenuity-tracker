import json
from flask import Flask, request
import redis

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

if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0')
