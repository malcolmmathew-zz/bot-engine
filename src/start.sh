# script to run after logging into heroku from within the docker container
docker exec -it bot-engine bash
python App/app.py