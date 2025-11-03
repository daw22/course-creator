from pymongo import MongoClient
from langgraph.checkpoint.mongodb import MongoDBSaver
from dotenv import load_dotenv
import os
import certifi
load_dotenv()

client = MongoClient(os.getenv("DB_URI"), tls=True, tlsCAFile=certifi.where())
db = client["course_creator"]
checkpointer = MongoDBSaver(db)