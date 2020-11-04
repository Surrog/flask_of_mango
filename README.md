# flask_of_mango
Basic flask microserver

## usage
* `http://localhost:5000/` return `Service running` when the flask server is running
* `http://localhost:5000/process_values` take a csv file in input and return a uuid
* `http://localhost:5000/status/<uuid>` return the current results computed by the server as a json or `{"error": "Id not found"}`

## install
* `git clone` local
* `sudo docker-compose build` to build the docker image
* `sudo docker-compose up -d` to start the flask & mongo server
* `sudo docker-compose down` to stop every docker images

## todo
* Do a cleanup service to purge old data stored in json
