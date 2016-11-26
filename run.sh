# set appropriate environment variables
source evars.sh

# run engine and retrieve user id
user_id="$(python engine.py)"
echo "USER ID: ${user_id}"

# change working directory
cd ./output/$user_id
