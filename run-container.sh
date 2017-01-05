# convenience script to start Docker container for application server
# need to exec into container and log into heroku
docker run -d -it -p 8080:5000 -v $PWD/src:/App --name=bot-engine flask-server
