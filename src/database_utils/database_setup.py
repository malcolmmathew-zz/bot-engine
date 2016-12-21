"""
	Clean database prior to running engine. Used strictly for engine testing.
"""
import os

from pymongo import MongoClient


def clean(mongo_host):
	"""
		Commands used to clean database prior to running engine.

		Parameters
		----------
		mongo_host : {string}
			mongo host ip which should be stored as env var
	"""
	client = MongoClient(mongo_host)
	db = client["botengine"]

	colls = db.collection_names(include_system_collections=False)

	for coll in colls:
		db[coll].drop()

	return True

if __name__ == '__main__':
	print clean(os.environ["MONGO_HOST"])
