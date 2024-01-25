import os
import redis
import openai
import time
import tiktoken
from openai2 import customChatCompletion1
from mariadb1 import encrypt_text1, decrypt_text1, get_key
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_password = os.getenv('REDIS_PASSWORD')
redis_db = int(os.getenv("REDIS_DB"))
stm_max_tokens = int(os.getenv("STM_MAX_TOKENS"))  # Convert to int
with open("ai_description1.txt", "r") as file:
	ai_description1 = file.read()

def num_tokens_from_messages(messages, model="gpt-4"):
	"""Returns the number of tokens used by a list of messages."""
	try:
		encoding = tiktoken.encoding_for_model(model)
	except KeyError:
		print("Warning: model not found. Using cl100k_base encoding.")
		encoding = tiktoken.get_encoding("cl100k_base")
	if model == "gpt-3.5-turbo":
		return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
	elif model == "gpt-4":
		return num_tokens_from_messages(messages, model="gpt-4-0314")
	elif model == "gpt-3.5-turbo-0301":
		tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
		tokens_per_name = -1  # if there's a name, the role is omitted
	elif model == "gpt-4-0314":
		tokens_per_message = 3
		tokens_per_name = 1
	else:
		raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for info on how messages are converted to tokens.""")
	num_tokens = 0
	for message in messages:
		num_tokens += tokens_per_message
		for key, value in message.items():
			num_tokens += len(encoding.encode(value))
			if key == "name":
				num_tokens += tokens_per_name
	num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
	return num_tokens

class ShortTermMemory1:
	def __init__(self, redis_host=redis_host, redis_port=redis_port, redis_password=redis_password, redis_db=redis_db):
		self.redis = redis.Redis(host=redis_host, port=redis_port, password=redis_password, db=redis_db)
		if self.redis.ping():
			print(f"Redis connection successful: \n{redis_host}, {redis_port}, DB_num in use: {redis_db}\n{str(self.redis.dbsize())} mem_key found.\n")
		else:
			print(f"Redis connection *NOT* successful!")

	def load_from_redis(self, mem_key1):
		buffMem1 = self.redis.get(f"buffMem1:{mem_key1}")
		if buffMem1 is None:
			decrypted_buffMem1 = f"""
User: Hello AI.
AI: Hi human, how can I assist you today?
User: Can you tell me what's 2+2?
AI: Sure! 2+2 is equals to 4!
User: Thanks! What's 1+1?
AI: 1+1 equals to 2!
			"""
			encrypted_buffMem1 = encrypt_text1(decrypted_buffMem1)
			self.redis.set(f"buffMem1:{mem_key1}", encrypted_buffMem1)
		else:
			decrypted_buffMem1 = decrypt_text1(buffMem1)
			# print(f"\nDEBUG! decrypted_buffMem1 from load_from_redis: \n{decrypted_buffMem1}")
		return decrypted_buffMem1.decode('utf-8') if isinstance(decrypted_buffMem1, bytes) else decrypted_buffMem1


	def save_and_update_context(self, user_input1, ai_reply1, user_id, workspace_id, platform_id):
		mem_key1 = f"{user_id}-{workspace_id}-{platform_id}"
		buffMem1 = self.load_from_redis(mem_key1)

		updated_buffMem1 = f"{buffMem1}\nUser: {user_input1}\nAI: {ai_reply1}"

		# Count tokens in updated conversation
		messages = [{"role": "User", "content": msg} if i % 2 == 0 else {"role": "AI", "content": msg}
					for i, msg in enumerate(updated_buffMem1.strip().split("\n")[1::2])]
		token_count = num_tokens_from_messages(messages)

		# If token count exceeds limit, trim oldest interactions until under limit
		while token_count > stm_max_tokens:
			updated_buffMem1 = "\n".join(updated_buffMem1.split("\n")[2:])  # removes the oldest message first, line by line, regardless of whether its user or ai.
			messages = [{"role": "User", "content": msg} if i % 2 == 0 else {"role": "AI", "content": msg}
						for i, msg in enumerate(updated_buffMem1.strip().split("\n")[1::2])]
			token_count = num_tokens_from_messages(messages)
		try:
			encrypted_updated_buffMem1 = encrypt_text1(updated_buffMem1)
			self.redis.set(f"buffMem1:{mem_key1}", encrypted_updated_buffMem1)
			print(f"\nEncrypted convo history updated in Redis.\n{str(self.redis.dbsize())} mem_key(s) found.")
		except Exception as e:
			print(f"Failed to save to Redis: {e}")	
	
	def genContextualResp(self, model1, user_input, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
		try:
			# Load the memory from Redis
			mem_key1 = f"{user_id}-{workspace_id}-{platform_id}"
			buffMem0 = self.load_from_redis(mem_key1)
			buffMem1 = str(buffMem0)

			# Generate the response based on the convo history aka buffMem1
			messages1 = [
				{"role": "system", "content": ai_description1},
				{"role": "system", "content": f"BY: \"{supername}\", USER-ID: \"{user_id}\" CHANNEL-ID: \"{channel_id}\" WORKSPACE-ID: \"{workspace_id}\" PLATFORM-ID: \"{platform_id}\""},
				{"role": "system", "content": "Convo history:\n" + buffMem1},
				{"role": "user", "content": "(It's " + timestring + ". Facts and info must be latest. Begin your reply with \"<@" + user_id + ">\". ) " + user_input},
				]

			response = openai.ChatCompletion.create(
				model=model1,
				messages=messages1,
				temperature=float(os.getenv("TEMPERATURE")),
				max_tokens=int(os.getenv("MAX_REPLY_TOKENS")),
				top_p=1,
				frequency_penalty=float(os.getenv("FREQ_PENALTY")),
				presence_penalty=float(os.getenv("PRES_PENALTY")),
			)
			string_reply1 = str(response.choices[0].message.content)
			tot_tokens1 = response['usage']['total_tokens']
			return string_reply1, tot_tokens1
		except Exception as e:
			string_reply1 = f"Error from stmem1.py, def genContextualResp: {e}"
			tot_tokens1 = 0
			return string_reply1, tot_tokens1