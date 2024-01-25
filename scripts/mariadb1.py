import os
from dotenv import load_dotenv
import mysql.connector
from contextlib import contextmanager
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
load_dotenv()

tablename1 = os.getenv("MARIADB_TABLE")

@contextmanager
def managed_cursor(conn):
	cursor = conn.cursor()
	try:
		yield cursor
	finally:
		cursor.close()

@contextmanager
def create_connection_context():
	conn = create_connection()
	try:
		yield conn
	finally:
		conn.close()

# Set up the MariaDB connection
def create_connection():
	try:
		conn = mysql.connector.connect(
			host=os.getenv("MARIADB_HOST"),
			port=os.getenv("MARIADB_PORT"),
			database=os.getenv("MARIADB_DB"),
			user=os.getenv("MARIADB_USER"),
			password=os.getenv("MARIADB_PASSWORD")
		)
	except mysql.connector.Error as err:
		if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
			# Database does not exist, let's create it
			conn = mysql.connector.connect(
				host=os.getenv("MARIADB_HOST"),
				port=os.getenv("MARIADB_PORT"),
				user=os.getenv("MARIADB_USER"),
				password=os.getenv("MARIADB_PASSWORD")
			)
			cursor = conn.cursor()
			cursor.execute(f"CREATE DATABASE {os.getenv('MARIADB_DB')} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
			conn.commit()
			# Now we can connect to the new database
			conn.database = os.getenv("MARIADB_DB")
		else:
			raise
	return conn


def test_mariadb1():
	conn = create_connection()
	cursor = conn.cursor()
	try:
		if cursor:
			print("Hermes RDB connection successful.")
	finally:
		cursor.close()
		conn.close()

def mariadb_totals():
	conn = create_connection()
	cursor = conn.cursor()
	try:
		if cursor:
			cursor.execute(f"SELECT COUNT(*) FROM {tablename1}")
			numOfMessages = cursor.fetchone()[0]  # Fetch the result and get the first value
			print(f"{numOfMessages} objects in RDB/{tablename1}.")
	finally:
		cursor.close()
		conn.close()

# Create the required table if it doesn't exist
def create_tables_if_not_exists():
	conn = create_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(f"""
			CREATE TABLE IF NOT EXISTS {tablename1} (
				cid VARCHAR(255) NOT NULL PRIMARY KEY,
				encrypted_text BLOB NOT NULL,
				supername VARCHAR(255),
				user_id VARCHAR(255),
				channel_id VARCHAR(255),
				workspace_id VARCHAR(255),
				platform_id VARCHAR(255),
				timestamp DOUBLE,
				timestring VARCHAR(255)
			)
		""")
			# Check for tot_tokens_table1 and create it if it doesn't exist
		cursor.execute(f"""
			CREATE TABLE IF NOT EXISTS tot_tokens_table1 (
				super_id VARCHAR(255) NOT NULL PRIMARY KEY,
				user_id VARCHAR(255),
				workspace_id VARCHAR(255),
				platform_id VARCHAR(255),
				total_tokens INT,
				daily_tokens INT,
				monthly_tokens INT,
				last_update_date DATE
			)
		""")
		conn.commit()
	finally:
		cursor.close()
		conn.close()
create_tables_if_not_exists()

# Insert a message into the database
def sql_insert_message(cid, encrypted_text, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
	conn = create_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(
			f"INSERT INTO {tablename1} (cid, encrypted_text, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
			(cid, encrypted_text, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
		)
		conn.commit()
	finally:
		cursor.close()
		conn.close()

def sql_get_message_by_cid(cid):
	conn = create_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(f"SELECT encrypted_text FROM {tablename1} WHERE cid = %s", (cid,))
		result = cursor.fetchone() # since you're fetching only one column, the returned result would be a tuple containing a single element.
		if result:
			return result[0] #  You need to extract the 'text' value from the tuple. Now, this is a string.
	finally:
		cursor.close()
		conn.close()

# Key management
def get_key():
	key1 = None
	if os.path.exists("./keys/mdb_n_redis_key1.key"):
		with open("./keys/mdb_n_redis_key1.key", "rb") as key_file:
			key1 = key_file.read()
			if len(key1) != 44: # a 32-byte url-safe base64-encoded key will be 44 characters long
				print(f"Invalid Key: {key1}, generating a new one.")
				key1 = None
	if not key1:
		key1 = Fernet.generate_key()
		with open("./keys/mdb_n_redis_key1.key", "wb") as key_file:
			key_file.write(key1)
	else:
		print(f"AES Encryption active.")
	return key1

# Encryption
def encrypt_text1(text1):
	bytes1 = text1.encode() # turns it into bytes, no longer a string!!!
	mdb_n_redis_key1 = get_key()
	cipher_suite1 = Fernet(mdb_n_redis_key1)
	encrypted_bytes1 = cipher_suite1.encrypt(bytes1)
	return encrypted_bytes1 # bytes are returned, not a string!!!

# Decryption
def decrypt_text1(encrypted_bytes1):
	mdb_n_redis_key1 = get_key()
	cipher_suite1 = Fernet(mdb_n_redis_key1)
	decrypted_str1 = cipher_suite1.decrypt(encrypted_bytes1)
	return decrypted_str1.decode() # a STRING is returned, not bytes!

def update_tot_tokens1(userid1, workspaceid1, platformid1, tot_tokens1):
	conn = create_connection()
	cursor = conn.cursor()

	try:
		# Create a super_id1
		super_id1 = f"{userid1}_{workspaceid1}_{platformid1}"
		
		# Check if the user exists in tot_tokens_table1
		cursor.execute("SELECT total_tokens, daily_tokens, monthly_tokens, last_update_date FROM tot_tokens_table1 WHERE super_id = %s", (super_id1,))
		result = cursor.fetchone()

		current_date = datetime.utcnow().date()

		if result:
			# Update the total tokens used by the user
			total_tokens, daily_tokens, monthly_tokens, last_update_date = result
			new_total_tokens = total_tokens + tot_tokens1

			if last_update_date == current_date:
				new_daily_tokens = daily_tokens + tot_tokens1
			else:
				new_daily_tokens = tot_tokens1

			if last_update_date and last_update_date.month == current_date.month:
				new_monthly_tokens = monthly_tokens + tot_tokens1
			else:
				new_monthly_tokens = tot_tokens1

			cursor.execute("UPDATE tot_tokens_table1 SET total_tokens = %s, daily_tokens = %s, monthly_tokens = %s, last_update_date = %s WHERE super_id = %s", (new_total_tokens, new_daily_tokens, new_monthly_tokens, current_date, super_id1))
		else:
			# If the user doesn't exist, create the user with the initial total tokens
			cursor.execute("INSERT INTO tot_tokens_table1 (super_id, user_id, workspace_id, platform_id, total_tokens, daily_tokens, monthly_tokens, last_update_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (super_id1, userid1, workspaceid1, platformid1, tot_tokens1, tot_tokens1, tot_tokens1, current_date))
			new_total_tokens = new_daily_tokens = new_monthly_tokens = tot_tokens1

		# Commit the changes
		conn.commit()

		# Print the updated total number of tokens
		print(f"New tokens: {tot_tokens1}, TODAY: {new_daily_tokens}, MONTH: {new_monthly_tokens}, TOTAL: {new_total_tokens}")

	finally:
		cursor.close()
		conn.close()
