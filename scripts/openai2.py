import os
from dotenv import load_dotenv
import openai
import time
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL")
max_reply_tokens = int(os.getenv("MAX_REPLY_TOKENS"))
temperature = float(os.getenv("TEMPERATURE"))
text_embedding_engine = os.getenv("TEXT_EMBEDDING_ENGINE")
frequency_penalty = float(os.getenv("FREQ_PENALTY"))
presence_penalty = float(os.getenv("PRES_PENALTY"))
with open("ai_description1.txt", "r") as file:
	ai_description1 = file.read()

def generate_embedding(user_input, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
	user_input1 = f"INPUT BY: \"{supername}\", USER-ID: \"{user_id}\" CHANNEL-ID: \"{channel_id}\" WORKSPACE-ID: \"{workspace_id}\" PLATFORM-ID: \"{platform_id}\" TIMESTAMP: \"{timestamp}\" TIMESTRING: \"{timestring}\" \nINPUT: {user_input}"
	for attempt in range(5):
		try:
			response = openai.Embedding.create(
				input=[user_input1],
				model=text_embedding_engine,
			)
			return response # a json, see https://platform.openai.com/docs/api-reference/embeddings/create
			# vector1 = response["data"][0]["embedding"] if wanna get just the pure vector
			# return vector1
		except Exception as e:
			if attempt < 4:
				time.sleep(2)
			else:
				print(f"Error from openai2.py, def generate_embedding: {e}")
				return None

def customChatCompletion1(model1, messages1):
	for attempt in range(5):
		try:
			response = openai.ChatCompletion.create(
			model=model1,
			messages=messages1,
			temperature=temperature,
			max_tokens=max_reply_tokens,
			top_p=1,
			frequency_penalty=frequency_penalty,
			presence_penalty=presence_penalty,
			stop=None,
			)
			string_reply1 = str(response.choices[0].message.content)
			tot_tokens1 = response['usage']['total_tokens']
			return string_reply1, tot_tokens1
		except Exception as e:
			if attempt < 4:
				time.sleep(2)
			else:
				string_reply1 = f"Error from openai2.py, def customChatCompletion1: {e}"
				tot_tokens1 = 0
				return string_reply1, tot_tokens1

def is_greeting(user_input):
	messages1 = [{"role": "user", "content": "QUERY1 is a user's query to an AI chatbot called Hermes. If the query is just a simple greeting, such as, but not limited to, ['hi', 'hey', 'howdy', 'sup', 'yo', 'whats up', 'greets', 'pleasure', 'hola', 'bonjour', 'ciao', 'namaste', 'aloha', 'shalom', 'salaam', 'konichiwa', or 'guten tag'], reply with a 'YES'. However, if the query is more than just a simple greeting, reply with a 'NO'. If the input is a simple w0, w1, or w2, reply with just a 'NO'. The query for you to evaluate accordingly is found within the curly brackets as follows:{ QUERY1: " + user_input + " }."}]
	string_reply1, tot_tokens1 = customChatCompletion1("gpt-3.5-turbo", messages1)
	# print(f"USER INPUT: {user_input}") # PASSED!
	print(f"\nSIMPLE GREETINGS?: {string_reply1}")
	if "yes" in string_reply1.lower():
		return True
	else:
		return False

def unsure(user_input, ai_reply):
	with open("./instructions/unsure1.txt", "r") as file:
		instr_unsure1 = file.read()
	messages1 = [{"role": "user", "content": f"{instr_unsure1}[ USER QUERY: \"{user_input}\", AI_REPLY1: \"{ai_reply}\".]"}]
	string_reply1, tot_tokens1 = customChatCompletion1("gpt-4", messages1)
	# print(f"AI_REPLY: {ai_reply}")
	print(f"\nIS AI UNSURE?: {string_reply1}")
	return string_reply1

''' 
	NOTES for UNSURENESS_DETECTED
	# messages = [{"role": "system", "content": "Your only task is to detect if the following text/ input shows any signs of low confidence, such as unsureness, uncertainty, unclearness, doubt, hesitation, confusion, insecurity, or the likes. Please strictly reply with just a 'YES' or a 'NO'."},

	1
	Can we assume that the following text/ input response is comprehensive and fully addresses the question at hand? Respond with 'YES' if it is comprehensive/ fully addresses, or 'NO' if it does not.

	2
	Does the following text/ input response provide a thorough and detailed reply to the given question? Respond with 'YES' for thorough/ detailed, or 'NO' for incomplete/ not detailed enough.

	3
	Does the following text/ input response provide a clear and concise answer to the given question? Reply with 'YES' for clear/ concise, or 'NO' for unclear/ not concise.

	4
	Is the following text/ input response comprehensive and detailed in addressing the given query? Respond with 'YES' for comprehensive/ detailed, or 'NO' for incomplete/ lacking details.
'''

'''
def is_unsure(response):
	unsure_phrases = [
		"couldn't find any information",
		"could not find any information",
		"unsure",
		"not sure",
		"not quite sure",
		"I don't have enough information",
		"I do not have enough information",
		"I don't know",
		"I do not know",
		"don't have access to information",
		"do not have access to information",
		"don't have access to information from the future",
		"do not have access to information from the future",
		"future events",
		"but as an AI language model",
		"provide more",
		"clarify",
		"clarity",
		"I'm sorry",
		"don't have the ability",
		"do not have the ability",
		"have any further details",
		"Unfortunately"
	]
	for phrase in unsure_phrases:
		if phrase.lower() in response.lower():
			return True
	return False
'''








'''def generate_response_g35t(user_input1, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
	messages1 = [
		{"role": "system", "content": ai_description1},
		{"role": "system", "content": "The input is by Name: \"" + supername + "\", of user-id \"" + user_id + "\", from channel \"" + channel_id + "\", workspace \"" + workspace_id + "\", platform \"" + platform_id + "\"."},
		{"role": "user", "content": "(It's " + timestring + ". Facts and info must be up to date, and you must stay within context.) " + input_text}
	]
	string_reply1, tot_tokens1 = customChatCompletion1("gpt-4", messages1)
	return string_reply1'''

'''def generate_response_g408k(user_input1, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring):
	messages1 = [
		{"role": "system", "content": ai_description1},
		{"role": "system", "content": "The input is by Name: \"" + supername + "\", of user-id \"" + user_id + "\", from channel \"" + channel_id + "\", workspace \"" + workspace_id + "\", platform \"" + platform_id + "\"."},
		{"role": "user", "content": "(It's " + timestring + ". Facts and info must be up to date, and you must stay within context.) " + input_text}
	]
	string_reply1, tot_tokens1 = customChatCompletion1("gpt-4", messages1)
	return string_reply1'''





'''def is_about_Hermes(user_input):
	messages1 = [{"role": "user", "content": "QUERY1 is a human user's query to an AI chatbot called Hermes. If the query contains questions about Hermes the AI Chatbot, reply with just a 'YES'. Or if the query contains questions about Kairos (aka kairos108 aka Kairos Siddhartha Kaizen) the creator/ coder/ programmer/ builder of Hermes, reply with just a 'YES'. However, if the query does not contain questions about Kairos or Hermes, reply with just a 'NO'. If it is uncertain if the query contains questions about Kairos or Hermes, reply with just a 'NO'. The query for you to evaluate accordingly is found within the curly brackets as follows:{ QUERY1: " + user_input + " }."}]
	string_reply1, tot_tokens1 = customChatCompletion1("gpt-4", messages1)
	print(f"USER INPUT: (redacted)")
	print(f"ABOUT HERMES?: {string_reply1}")
	if "yes" in string_reply1.lower():
		return True
	else:
		return False'''
	