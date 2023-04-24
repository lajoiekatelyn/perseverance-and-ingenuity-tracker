# Perseverance and Ingenuity Tracker REST API
## Purpose

In 2020 NASA sent a Mars rover, Perseverance, and a robotic helicopter, Ingenuity, to explore Mars and its habitability. NASA funded this project to achieve four main objectives: determine if there was life on Mars at some point, characterize past and current climate, characterize the geology of Mars, and prepare for human exploration. It has been nearly three years and thus a lot of data has been collected. 

Combining information from both Perseverance and Ingenuity's datasets could potentially yield a richer set of information. However, it is currently very difficult to work with two large and seperate datasets. Through this project we seek to close the gap by being able to emphasize areas where the datasets overlap. While we do not have access the data collected by the two robots, we hope that researchers can build upon this app in order to make important discoveries regarding Mars and its habitability. Furthermore, this project shows the potential that can result from the synchronization of data from various robots when studying an unknown environment. 

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

## Docker

To ensure functionality across macnines, this app is containerized according to the included DockerFile and launched according to the included docker-copose.yml file. To run the app as an end user, please refer to the Pull the Docker Image and docker-compose sections below. To develop using the app in this repo, please refer to the DockerFile section below.


### Pull and Build the Docker Image
As an end user, running the app has four simple steps. First, change the Redis database client host in the `gene_api.py` script from `klajoie-test-redis-service` to `redis-db`. Then, pull the image from the Docker Hub and then build the image. To do so, please run the following command
```
$ docker pull lajoiekatelyn/gene_flask_app:1.0
```
and then, in the root of the repo,
```
$ docker build -t lajoiekately/gene_flask_app:1.0 .
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
$ docker build -t <docker_username>:gene_flask_app:<version_number>
```
where `<docker_username>` is your Docker username and `<version_number>` is the verion of the image that you wish to build.

#### docker-compose for Developers
If you develop and push a new Docker image to Docker Hub, you will need to change the name of the Docker image in docker-compose.yml to the name of the image that you pushed.

NOTE: for the purpose of using docker-compose, the host declared for the Redis client in the get_redis_client() funciton in gene_api.py is set to `redis-ip`. In order to develop using Flask, change the host to `127.0.0.1`. Then, when it comes time to use docker-compose again, change it back to `redis-ip`  for correct use with Kubernetes. Additionally, if the service used to reach the Redis database in Kubernetes is changed, update the name of the service from `klajoie-test-redis-service` to the new name in both `docker-compose.yml` and `klajoie-test-flask-deployment.yml` for use with Kubernetes.


## Kubernetes
To run this app on a Kubernetes cluster, please follow the instructions below.

### Deployment
Each yaml file in this repo, save for `docker-compose.yml`, is a file that needs to be applied to Kubernetes. To do so, enter the following commands in the console from which you have Kubernetes access:
```
$ kubectl apply -f klajoie-test-redis-deployment.yml
$ kubectl apply -f klajoie-test-pvc.yml
$ kubectl apply -f klajoie-test-flask-deployment.yml
$ kubectl apply -f klajoie-test-redis-service.yml
$ kubectl apply -f klajoie-test-flask-service.yml
$ kubectl apply -f klajoie-test-python-debug.yml
```
The console should output confirmation that you properly applied each deployment, persistent volume control, service, etc after each `kube apply -f` command and then you should be good to go using Kubernetes!
NOTE: if users wish to user their own Flask API in the kubernetes cluster, they must change the image being pulled in `klajoie-test-flask-deployment` to their image on Docker Hub and then re-apply the kubernetes depolyment.

### Kubernetes Usage
To use the cluster, first run the following comand
```
$ kubectl get pods
klajoie-test-flask-deployment-57648c5759-t9x5t   1/1     Running   0               102m
klajoie-test-flask-deployment-57648c5759-vjzl7   1/1     Running   0               102m
klajoie-test-redis-deployment-654c66bcb6-smzjm   1/1     Running   0               104m
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

where you can use any of the commands below, under Usage, replacing `localhost` with `klajoie-test-flask-service`. An example of this can be seen  in the usage section. 

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
| `/map` | POST | Create map with path data based on inputted sols |
| | GET | Return a dictionary containing link to the image |
| | DELETE | Delete map data in redis |
