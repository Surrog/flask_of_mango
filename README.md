# flask_of_mango
Basic flask microserver

## usage
* `http://localhost:5000/` return `Service running` when the flask server is running
* `http://localhost:5000/process_values` take a csv file in input and return a uuid
* `http://localhost:5000/status/<uuid>` return the current results computed by the server as a json or `{"error": "Id not found"}`

## install
* `git clone` local
* `./build.sh` to build the docker image
* `./start.sh` to start the flask server
* `./stop.sh` to stop the server

## todo
* Actually using mongodb, create a docker compose to handle multiple docker instances
* Move threaded process in a asyncio python coroutine
* Do a cleanup service to purge old data stored in json
