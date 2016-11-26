# set appropriate environment variables
source evars.sh

# run engine and retrieve user id
user_id="$(python engine.py)"
echo "USER ID: ${user_id}"

# change working directory
cd ./output/$user_id

# application deployment - heroku
heroku create
git push heroku master
web_url="$(heroku info -s | grep web_url | cut -d= f2)"
echo "WEB URL: ${web_url}"
