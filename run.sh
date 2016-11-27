# set appropriate environment variables
source evars.sh

# clean database - only for testing
python database_setup.py

# run engine and retrieve user id
engine_output="$(python engine.py)"
output_arr=(${engine_output//,/ })
user_id=${output_arr[0]}
pat=${output_arr[1]}
vt=${output_arr[2]}
echo "USER ID: ${user_id}"
echo "PAGE ACCESS TOKEN: ${pat}"
echo "VERIFY TOKEN: ${vt}"

# copy output directory to deployment sandbox
rm -rf ../bot-apps/$user_id
cp -r ./output/$user_id ../bot-apps/$user_id

# change working directory
cd ../bot-apps/$user_id
git init

# application deployment
heroku create
heroku config:add PAGE_ACCESS_TOKEN=$pat
heroku config:add VERIFY_TOKEN=$vt
git add .
git commit -m "init commit - required"
git push heroku master
web_url="$(heroku info -s | grep web_url | cut -d= -f2)"
echo "WEB URL: ${web_url}"