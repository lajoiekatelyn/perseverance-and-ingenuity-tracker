# Perseverance and Ingenuity Tracker REST API
## Purpose

In 2020 NASA sent a Mars rover, Perseverance, and a robotic helicopter, Ingenuity, to explore Mars and its habitability. NASA funded this project to achieve four main objectives: determine if there was life on Mars at some point, characterize past and current climate, characterize the geology of Mars, and prepare for human exploration. It has been nearly three years and thus a lot of data has been collected. 

Combining information from both Perseverance and Ingenuity's datasets yields a richer dataset. However, it is currently very difficult to work with two large and seperate datasets. Through this project we seek to close the gap by being able to emphasize areas where the datasets overlap. While we do not have access the data collected by the two robots, we hope that researchers can build upon this app in order to make important discoveries regarding Mars and its habitability. Furthermore, this project shows the potential that can result from the synchronization of data from various robots when studying an unknown environment. 

## Data 

The public [data](https://mars.nasa.gov/mars2020/mission/where-is-the-rover/) is maintained and provided by NASA. It provides real-time location of both Perseverance and Ingenuity. The website also provides other information regarding rock samples, waypoints, oaths, and more. For this project we are only using the rover path and helicopter flight path. The rover path data consist of sols, clock, and latitude/logitude coordinates. The helicopter path data consist of sols, flight, clock, and latitude/longitude/altitude coordinates.

## Files

## Flask
This program uses the Python Flask library. Flask is a web framework used to develop generalized web applications. To install Flask, please enter the following command into your terminal:

```
$ pip3 install --user flask
```
## Redis

This script uses the Redis, a NoSQL database, to store all app data to ensure that it is not lost when the Flask app stops running and allow for multiple processes to access the data at once. If the Redis Python library is not already installed on your machine and you plan on doing development with this repo, please install it using
```
pip3 install redis
```
otherwise, Docker will take care of the Redis image for this application.

## Imgur API

The Imgur API is a RESTful API that is based on HTTP requests and it returns JSON responses. To allow the user to see the plots they produce the Flask application makes a requests to the url https://api.imgur.com/3/upload. The Flask app then return to the user the response from the Imgur API which includes a link to the image among other information

## Docker

To ensure functionality across macnines, this app is containerized according to the included DockerFile and launched according to the included docker-copose.yml file. To run the app as an end user, please refer to the Pull the Docker Image and docker-compose sections below. To develop using the app in this repo, please refer to the DockerFile section below.


### Pull and Build the Docker Image
As an end user, running the app has four simple steps. First, change the Redis database client host in the `app.py` script from `final-redis-service` to `redis-db`. Then, pull the image from the Docker Hub and then build the image. To do so, please run the following command
```
$ docker pull lajoiekatelyn/perseverance_and_ingenuity_tracker:kube
```
and then, in the root of the repo,
```
$ docker build -t lajoiekatelyn/perseverance_and_ingenuity_tracker:kube .
```
Then the image should be good to go.

### docker-compose
To launch the app alongside Redis, please run the following command in the root of the directory
```
$ docker-compose up -d
```
to run the app and Redis in the background. Then, to terminate the app and Redis,
```
$ docker-compose down
```
### DockerFile
To build upon this repo, any new package used in the main script will need to be added to the DockerFile. Then, the docker image will need to be rebuilt. To do so,
```
$ docker build -t <docker_username>:perseverance_and_ingenuity_tracker:<version_number>
```
where `<docker_username>` is your Docker username and `<version_number>` is the verion of the image that you wish to build.

#### docker-compose for Developers
If you develop and push a new Docker image to Docker Hub, you will need to change the name of the Docker image in docker-compose.yml to the name of the image that you pushed from the build above.

NOTE: for the purpose of using docker-compose, the host declared for the Redis client in the get_redis_client() funciton in gene_api.py is set to pull from the Kubernetes environment using `os`. In order to develop using Flask, change the host to `127.0.0.1`. Then, when it comes time to use docker-compose again, change it back to `redis_ip`, the variable which `os` pulls from the environment, for correct use with Kubernetes. Additionally, if the service used to reach the Redis database in Kubernetes is changed, update the name of the service from `final-redis-service` to the new name in both `docker-compose.yml` and `final-flask-deployment.yml` for use with Kubernetes.


## Kubernetes
To run this app on a Kubernetes cluster, please follow the instructions below.

### Deployment
Each yaml file in this repo, save for `docker-compose.yml`, is a file that needs to be applied to Kubernetes. To do so, enter the following commands in the console from which you have Kubernetes access:
```
$ kubectl apply -f final-redis-deployment.yml
$ kubectl apply -f final-pvc.yml
$ kubectl apply -f final-flask-deployment.yml
$ kubectl apply -f final-redis-service.yml
$ kubectl apply -f final-flask-service.yml
$ kubectl apply -f final-python-debug.yml
```
The console should output confirmation that you properly applied each deployment, persistent volume control, service, etc after each `kube apply -f` command and then you should be good to go using Kubernetes!
NOTE: if users wish to user their own Flask API in the kubernetes cluster, they must change the image being pulled in `final-flask-deployment` to their image on Docker Hub and then re-apply the kubernetes depolyment.

### Kubernetes Usage
To use the cluster, first run the following comand
```
$ kubectl get pods
final-flask-deployment-57648c5759-t9x5t   1/1     Running   0               102m
final-flask-deployment-57648c5759-vjzl7   1/1     Running   0               102m
final-redis-deployment-654c66bcb6-smzjm   1/1     Running   0               104m
py-debug-deployment-f484b4b99-r9vff              1/1     Running   0               8h
```

Note the python debug deployment and use it to access the cluster:
```
$ kubectl exec -it py-debug-deployment-f484b4b99-r9vff -- /bin/bash
```

You will end up in a terminal something like:
```
root@py-debug-deployment-f484b4b99-r9vff:/#
```

where you can use any of the commands below, under Usage, replacing `localhost` with `final-flask-service`. An example of this can be seen  in the usage section. 

## Deploying and testing the application

## Using the the application
Here is a table of the routes:

| Route | Method | Description |
| --- | --- | --- |
| `/data` | POST | Store data into redis |
| | GET | Return all data from redis as a json-formatted list from both path datasets |
| | DELETE | Delete all data in redis |
| `/rover` | GET | Return json-formatted list of the rover path data |
| `/rover/sols` | GET | Return json-formatted list of all the sols where the rover was operational |
| `/rover/sols/<string:sol>` | GET | Return dictionary with all the information in the rover dataset associated with that sol |
| `/heli/` | GET | Return json-formatted list of the heli path data |
| `/helicopter/flights` | GET | Return json-formatted list of the heli flights|
| `/helicopter/flights/<string:flight>` | GET | Return dictionary with information related to a given flight|
| `/heli/sols` | GET | Return json-formatted list of all the sols where the heli was operational |
| `/heli/sols/<string:sol>` | GET | Return dictionary with all the information in the heli dataset associated with that sol |
| `/rover/sols/<string:sol>/helicopter` | GET | Return dictionary containing the shortest distance between the robots |
| `/both_deployed` | GET | Return list where both Perseverance and Ingenuity were deployed |
| `/map?jid=<jid_string> ` | GET | Request information on an image generated by jid_string |
| | DELETE | Delete image generated by <jid_string> from the database. |
| `/jobs` | POST | Post a job specifying {"upper": upper_sol_limit, "lower": lower_sol_limit} to the queue. |

### /data [POST]
```
$ curl -X POST localhost:5000/data
Data loaded into db.
```
### /data [GET]
```
$ curl localhost:5000/data
  {
    "geometry": {
      "coordinates": [
        [
          77.451388,
          18.442665
        ],
        [
          77.449155,
          18.441573
        ],
        [
          77.449181,
          18.441336
        ],
        [
          77.449943,
          18.44166
        ]
      ],
      "type": "LineString"
    },
    "properties": {
      "Flight": 6,
      "Length_m": 202.363,
      "SCLK_END": 675019237.6,
      "SCLK_START": 675019097.7,
      "Sol": 91
    },
    "type": "Feature"
  }
]
```
### /data [DELETE]
```
$ curl -X DELETE localhost:5000/data
Data deleted.
```
### /rover/sols
```
$ curl localhost:5000/rover/sols
[
  "sol:0014",
  "sol:0015",
  "sol:0016",
  "sol:0020",
  "sol:0023",
  "sol:0029",
  "sol:0031",
  "sol:0032",
  "sol:0033",
  "sol:0034",
  "sol:0043",
  "sol:0044",
  ...
]
```
### /rover/sols/<string:sol>
```
$ curl localhost:5000/rover/sols/sol:0014
{
  "geometry": {
    "coordinates": [
      [
        77.450886,
        18.444627,
        -7.8e-05
      ],
      [
        77.450897,
        18.444617,
        -7.8e-05
      ],
      [
        77.45091,
        18.444606,
        -7.8e-05
      ],
      ...
}
```
### /helicopter/flights
```
$ curl localhost:5000/helicopter/flights
[
  "Flight:41",
  "Flight:13",
  "Flight:12",
  "Flight:48",
  "Flight:16",
  "Flight:30",
  "Flight:47",
  "Flight:37",
  ...
]
```
### /helicopter/flights/<string:flight>
```
$ curl localhost:5000/helicopter/flights/Flight:41
{
  "geometry": {
    "coordinates": [
      [
        77.407122,
        18.458697
      ],
      [
        77.405825,
        18.459777
      ],
      [
        77.407091,
        18.459016
      ]
    ],
    "type": "LineString"
  },
  "properties": {
    "Flight": 41,
    "Length_m": 181.349,
    "SCLK_END": 728119180,
    "SCLK_START": 728119071,
    "Sol": 689
  },
  "type": "Feature"
}
```
### /heli/sols
```
$ curl localhost:5000/helicopter/sols
[
  "sol:0058",
  "sol:0061",
  "sol:0064",
  "sol:0069",
  "sol:0076",
  "sol:0091",
  "sol:0107",
  "sol:0120",
  "sol:0133",
  ...
]
```
### `/heli/sols/<string:sol>
```
$ curl localhost:5000/helicopter/sols/sol:0714
{
  "geometry": {
    "coordinates": [
      [
        77.398408,
        18.472231
      ],
      [
        77.398368,
        18.474394
      ],
      [
        77.392373,
        18.477141
      ]
    ],
    "type": "LineString"
  },
  "properties": {
    "Flight": 45,
    "Length_m": 502.6,
    "SCLK_END": 730342605.9,
    "SCLK_START": 730342461.3,
    "Sol": 714
  },
  "type": "Feature"
}
```
### both_deployed
```
$ curl localhost:5000/both_deployed
[
  "sol:0398",
  "sol:0362",
  "sol:0717",
  "sol:0107",
  "sol:0418",
  "sol:0714",
  "sol:0681",
  "sol:0384",
  "sol:0708",
  "sol:0414",
  "sol:0388",
  "sol:0091"
]
```
### /rover/sols/<string:sol>/helicopter
```
$ curl localhost:5000/rover/sols/sol:0091/helicopter
{
  "shortest_dist": 85.31574053466534
}
```
### /map [POST]
### /map [GET]
### /map [DELETE]
