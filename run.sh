# set appropriate environment variables
source evars.sh

# run engine and retrieve user id
user_id="$(python engine.py)"
echo "USER ID: ${user_id}"

# copy output directory to deployment sandbox
cp -r ./output/$user_id ../bot-apps/$user_id

# change working directory
cd ../bot-apps/$user_id
git init

# application deployment - heroku
heroku create
git add .
git commit -m "init commit - required"
git push heroku master
web_url="$(heroku info -s | grep web_url | cut -d= -f2)"
echo "WEB URL: ${web_url}"