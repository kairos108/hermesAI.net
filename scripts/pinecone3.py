import os

# import pinecone
from pinecone import Pinecone

import time
import openai
from openai2 import generate_embedding
import numpy as np
import datetime
import threading
from mariadb1 import *
from uuid import uuid4

# Added imports for environment variables and OpenAI API call
from dotenv import load_dotenv

load_dotenv()

pinecone_url = os.getenv("PINECONE_URL")
pinecone_index = os.getenv("PINECONE_INDEX")
namespace1 = os.getenv("PINECONE_NAMESPACE")

# pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))
pcone0 = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)
pcone1 = pcone0.Index(pinecone_index)


"""
# PINECONE NEW VERSION IS MESSING UP WITH ALL MY CODES BELOW. NO TIME TO REDO CODE. JUST CREATE PINECONE INDEX MANUALLY.

# Create Pinecone index
if pinecone_index not in pcone0.list_indexes():
	pcone0.create_index(
		name=pinecone_index,
		dimension=int(os.getenv("PINECONE_DIMENSIONS")),
		metric=os.getenv("PINECONE_METRIC"),
		spec=spec
	)
	print("NEW VDB index created.")
"""

# Connect to the index
# index1 = pcone1.Index(index_name=pinecone_index)
index1 = pcone1
print("Hermes VDB connection successful.")
test_mariadb1()
index_stats = index1.describe_index_stats(namespace=namespace1)
total_vector_count = index_stats["total_vector_count"]
print(f"VDB Details:\n{index1.describe_index_stats(namespace=namespace1)}")
mariadb_totals()
batch_upsert_COLLECTION = []
batch_INsert_COLLECTION = []

def pinecone_batch_upsert_INsert():
	global batch_upsert_COLLECTION
	global batch_INsert_COLLECTION	
	print("\nATTEMPTING BATCH UPSERT.")
	
	# not important.
	current_datetime = datetime.now()
	print("Now: ", current_datetime)
	
	total_vectors = len(batch_upsert_COLLECTION)
	total_texts = len(batch_INsert_COLLECTION)
	print(f"Cache status: {str(total_vectors)}:{str(total_texts)} of 33 vectors.")
	if batch_upsert_COLLECTION and total_vectors == total_texts:
		print(f"*{str(total_vectors)}:{str(total_texts)}* upsert:INsert object(s) in the collection.")
		# Determine the number of batch upserts needed
		batch_size = 99
		num_batches = (total_vectors + batch_size - 1) // batch_size
		for i in range(num_batches):
			start = i * batch_size
			end = min((i + 1) * batch_size, total_vectors)
			batch = batch_upsert_COLLECTION[start:end]
			INbatch = batch_INsert_COLLECTION[start:end]
			
			#batch upserts into pinecone
			index1.upsert([(item[0], item[1], item[2]) for item in batch], namespace=namespace1)

			# batch inserts into MariaDB
			for item in INbatch:
				sql_insert_message(*item)

			print(f"Batch {i + 1} of {num_batches} upserted/INserted successfully.")
		batch_upsert_COLLECTION.clear()
		batch_INsert_COLLECTION.clear()
		print(f"*{len(batch_upsert_COLLECTION)}:{len(batch_INsert_COLLECTION)}* upsert:INsert object(s) left in the collection.")
		print(f"VDB Details:\n{index1.describe_index_stats(namespace=namespace1)}")		
		mariadb_totals()
	elif total_vectors != total_texts:
		print("Error!: upserts != INserts .")
	else:
		print("Nothing to upsert/INsert.")
		print(f"VDB Details: {index1.describe_index_stats(namespace=namespace1)}")		
		mariadb_totals()

def pinecone_queue_convo(text, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
	global batch_upsert_COLLECTION
	global batch_INsert_COLLECTION
	
	# TOO LONG. max tokens on g35t cant handle!
	# text1 = f"SPEAKER: \"{supername}\", USER-ID: \"{user_id}\" CHANNEL-ID: \"{channel_id}\" WORKSPACE-ID: \"{workspace_id}\" PLATFORM-ID: \"{platform_id}\" TIMESTAMP: \"{timestamp}\" TIMESTRING: \"{timestring}\" \nINPUT: {text}"

	text0 = f"SPEAKER: \"{supername}\", TIMESTRING: \"{timestring}\" \nINPUT: {text}"
	
	# Pinecone stuff
	vector1_json = generate_embedding(text0, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
	vector1 = vector1_json["data"][0]["embedding"] 
	model = vector1_json["model"]
	total_tokens = vector1_json["usage"]["total_tokens"]	
	metadata = {
		"supername": supername,
		"user_id": user_id,
		"channel_id": channel_id,
		"workspace_id": workspace_id,
		"platform_id": platform_id,
		"timestamp": timestamp,
		"timestring": timestring
	}

	# After generating and queueing the vector, NOW then should you encrypt the text.
	encrypted_text = encrypt_text1(text0) # these are BYTES! not a string!
	# SUCCESS. print(f"DEBUG_encrypted_text: {text1}")

	convo_id = f"id-{str(uuid4())}"
	batch_upsert_COLLECTION.append((convo_id, vector1, metadata))
	batch_INsert_COLLECTION.append((convo_id, encrypted_text, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring))
	print(f"*{len(batch_upsert_COLLECTION)}:{len(batch_INsert_COLLECTION)}* upsert:INsert object(s) in the collection.")
	print("Awaiting timer or trigger to batch upsert/INsert.")

def pinecone_batch_upsert_loop_66():
	while True:
		time.sleep(20)
		if len(batch_upsert_COLLECTION) >= 33: #used to be 66, hence the name. still not sure what number to use. "Each vector consists of 1536 float values, and assuming each float value consumes 4 bytes, the size of a single vector is approximately 6KB (1536 * 4 bytes). With 33 vectors in the queue, the total size would be approximately 198KB (33 * 6KB). This should not cause any significant memory issues for your server." Also needs to balance out getting rate-limited by Pinecone for doing upserts too often too quickly.
			print("More than 33 vectors detected in collection...")
			pinecone_batch_upsert_INsert()
			print(f"*{len(batch_upsert_COLLECTION)}:{len(batch_INsert_COLLECTION)}* upsert:INsert object(s) in the collection.")
		else:
			print(f"Cache status: {str(len(batch_upsert_COLLECTION))} of 33 vectors.")

def pinecone_batch_upsert_loop():
	while True:
		time.sleep(60)
		pinecone_batch_upsert_INsert()

def fetch_similar_items(query_embedding, top_k=int(os.getenv("NUM_OF_MEMORIES"))):
	# Fetch the highest-scoring amount=top_k similar messages from the past, from pinecone. Values=False means to just fetch the id's and scores - dont return the actual vectors themselves, which are voluminous.
	matches = index1.query(vector=query_embedding, top_k=int(os.getenv("NUM_OF_MEMORIES")), include_values=False, namespace=namespace1)
	print(f"\nFound {len(matches['matches'])} matching vectors in the VDB...")
	print("Matching vectors: " + str(matches)[:333] + "...")

	# Fetch the messages from MariaDB using the CIDs
	messages = [
		{
			"id": match["id"],
			"score": match["score"],
			"message": sql_get_message_by_cid(match["id"]),
		}
		for match in matches["matches"]
	]

	# Format the messages as a string
	results_string1 = ""
	for message in messages:
		results_string1 += f"""\n[{message['id']}] Relevance/ Similarity Score: \"{message['score']}\"  Past-conversation values as follows... \n{decrypt_text1(message['message'])}\n"""
	return results_string1