# set appropriate environment variables
source evars.sh

# clean database - only for testing
python database_setup.py

# run engine and retrieve user id
user_id="$(python engine.py)"
echo "USER ID: ${user_id}"

# change working directory
cd ./output/$user_id
ls
