import re, random, os, time, datetime
from slack_bolt import App
from slack_sdk import WebClient
from search1 import *
from openai2 import *
from pinecone3 import *
from slack_sdk.errors import SlackApiError
from stmem1 import ShortTermMemory1
from basic_commands1 import welcome_message, say_greetings1
from dotenv import load_dotenv
load_dotenv()

bolt_app = App(token=os.getenv("SLACK_BOT_TOKEN"))
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
platform_id = "slack"
AI_name = os.getenv("AI_NAME")
bot_user_id = AI_name # might be problematic. keep an eye out. prefer to NOT have to include buid into the code.

stm1 = ShortTermMemory1()

def timestamp_to_datetime(unix_time):
	return datetime.fromtimestamp(unix_time).strftime("%A, %B %d, %Y at %I:%M%p %Z")

def custom_say(user_input1, ai_reply1, user_id, channel_id, workspace_id):
	bolt_app.client.chat_postMessage(channel=channel_id, text=ai_reply1, unfurl_links=False)
	timestamp = time.time()
	timestring = timestamp_to_datetime(timestamp)
	pinecone_queue_convo(ai_reply1, AI_name, bot_user_id, channel_id, workspace_id, platform_id, timestamp, timestring) # this is for storing the AI's reply. storing of User's input has already been done separately in def handle_slack_events
	stm1.save_and_update_context(user_input1, ai_reply1, user_id, workspace_id, platform_id)

def handle_slack_events(body, say):
	fulltext0 = body["event"]["text"].strip()
	patternToOverwrite = r'<@[^>]*>'
	fulltext1 = re.sub(patternToOverwrite, f"@{AI_name}", fulltext0)
	user_input = ' '.join(fulltext1.split()[1:]) # stripped bare, just purely the input, without the @Hermes
	user_id = body["event"]["user"]
	channel_id = body["event"]["channel"]
	workspace_id = slack_client.team_info()["team"]["id"]	
	platform_id = "slack"
	timestamp = time.time()
	timestring = timestamp_to_datetime(timestamp)
	supername0 = slack_client.users_info(user=user_id)
	supername = f"{supername0['user']['name']} (Fullname: {supername0['user']['real_name']})"
	mem_key1 = f"{user_id}-{workspace_id}-{platform_id}"
	stm1.load_from_redis(mem_key1)

	# Get all public channels
	public_channels = []
	cursor = None
	while True:
		try:
			response = slack_client.conversations_list(types='public_channel', cursor=cursor)
			public_channels.extend(response['channels'])
			cursor = response.get('response_metadata', {}).get('next_cursor')
			if not cursor:
				break
		except SlackApiError as e:
			print(f"Error fetching channels: {e}")
			break
	# Check if current channel is public
	is_public_channel = any(channel['id'] == channel_id for channel in public_channels)
	# List of hardcoded allowed private channels
	allowed_private_channels_str = os.getenv("ALLOWED_PRIVATE_CHANNELS")
	allowed_private_channels = allowed_private_channels_str.split(",")

	if not is_public_channel and channel_id not in allowed_private_channels:
		text1 = f"""
<@{user_id}> Apologies, human. Non-public channels are disallowed from using Hermes at this testing phase.

Feel free to create a _PUBLIC_ personal channel, where its just you and Hermes, and continue chatting.
> 1. Right-click on CHANNELS on the left sidebar
> 2. Create a PUBLIC channel
> 3. Type in `/invite @Hermes` and press enter

If you are an organization, the HermesAI team will create a new _PRIVATE_ channel for your testing purposes (a HermesAI personel will always be present with you inside that new channel).

Reach out to a HermesAI team member if you need help.
Thank you for your understanding and support!
		"""
		bolt_app.client.chat_postMessage(channel=channel_id, text=text1)
		return
	elif user_input == "11":
		text1 = f"<@{user_id}> Yes, I see that you typed in 11."
		bolt_app.client.chat_postMessage(channel=channel_id, text=text1)
		return
	elif "search4" in fulltext1.lower():
		bolt_app.client.chat_postMessage(channel=channel_id, text="Searching the Akashic Records...")
		search_results = search_web(search_term=user_input)
		bolt_app.client.chat_postMessage(channel=channel_id, text=search_results, unfurl_links=False)
		return
	elif "essay4" in fulltext1.lower():
		bolt_app.client.chat_postMessage(channel=channel_id, text="One sec...")
		ai_reply, tot_tokens1 = stm1.genContextualResp("gpt-3.5-turbo", user_input, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
		update_tot_tokens1(user_id, workspace_id, platform_id, tot_tokens1)
		bolt_app.client.chat_postMessage(channel=channel_id, text=ai_reply, unfurl_links=False)
		return
	elif is_greeting(fulltext1):
		ai_reply1 = say_greetings1(fulltext1)
		bolt_app.client.chat_postMessage(channel=channel_id, text=ai_reply1)
		stm1.save_and_update_context(user_input, ai_reply1, user_id, workspace_id, platform_id)
		return
	else:
		pinecone_queue_convo(fulltext1, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
		
		"""
		NOTES FOR EVALUATORS:
		originally, and it worked fine in April - July 2023, Hermes will evaluate his "initial reply" to the user, and if there's a hint of "unsureness", he will NOT send the reply to the user.
		instead, he will then conduct a live web search on his own, and then formulate a "new reply" to the user.
		IF the new reply is still showing uncertainty, he will then proceed on to searching his vector database longterm memory, and then formulate yet another "new reply".
		
		but eversince openai updated chatgpt, and pinecone updated to serverless, everything's a mess now, and im unable to find the time to update/ tweak the codes to match the new versions.
		
		(i also planned to make Hermes actually formulate a proper, contextually-accurate, search query, before conducting the live-search, but alas, my job schedule is hectic.)
		"""
		
		# OPENAI UPDATED CHATGPT AND PINECONE UPDATED TO SERVERLESS AND NOW THE "UNSURE" OR "MY KNOWLEDGEBASE" REPLY IS ALL MESSED UP AND DIFFERENT.
		# Since I dont have time (hectic work schedule), i'm unable to investigate and make changes/ updates/ tweaks,
		# so i am removing this one step, where there's an "initial reply" by Hermes to evaluate if his reply is "unsure".
		"""
		ai_reply, tot_tokens1 = stm1.genContextualResp("gpt-4", user_input, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
		update_tot_tokens1(user_id, workspace_id, platform_id, tot_tokens1)
		print("\nDEBUG1: THE FIRST INITIAL ai_reply: " + ai_reply)
		is_unsure1 = unsure(user_input, ai_reply)
		"""
		
		# hard-coding is_unsure1 to "YES1". :(
		is_unsure1 = "YES1"
		if "yes1" not in is_unsure1.lower():
			# custom_say(user_input, ai_reply, user_id, channel_id, workspace_id)
			return
		else:
			say("One sec...")
			
			# SEARCH SECTION
			search_results = search_web(user_input)
			print(f"DEBUG_search_results: {search_results[:333]}...")
			with open("./instructions/webSearch.txt", "r") as file:
				instructions_webSearch = file.read()
			enhanced_prompt = f"""
				Instructions: {instructions_webSearch} 
				Here are the 3 variables: 
				SPEAKER: \"{supername}\" 
				INPUT1: \"{user_input}\" 
				SEARCH1: \"{search_results}\"
			"""			
			# search_response, tot_tokens1 = stm1.genContextualResp("gpt-4", enhanced_prompt, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
			messages1 = [{"role": "user", "content": f"{enhanced_prompt}"}]
			search_response, tot_tokens1 = customChatCompletion1("gpt-3.5-turbo", messages1)
			update_tot_tokens1(user_id, workspace_id, platform_id, tot_tokens1)
			print("\nDEBUG_search_response: " + search_response)

			# MEMORIES SECTION
			query_vector_json = generate_embedding(user_input, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
			query_vector1 = query_vector_json["data"][0]["embedding"]
			similars_string1 = fetch_similar_items(query_vector1)				
			with open("./instructions/memories1.txt", "r") as file:
				instructions_memories1 = file.read()
			enhanced_prompt = f"""
				Instructions: {instructions_memories1}
				Here are the 3 variables:
				SPEAKER: \"{supername}\" 
				INPUT1: \"{user_input}\" 
				MEMORIES1: \"{similars_string1}\"
			"""				
			# memories_response, tot_tokens1 = stm1.genContextualResp("gpt-4", enhanced_prompt, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
			messages1 = [{"role": "user", "content": f"{enhanced_prompt}"}]
			memories_response, tot_tokens1 = customChatCompletion1("gpt-3.5-turbo", messages1)
			update_tot_tokens1(user_id, workspace_id, platform_id, tot_tokens1)
			print("\nDEBUG_memories_response: " + memories_response)

			# HYBRID RESPONSE 1
			with open("./instructions/hybridSearch1.txt", "r") as file:
				instructions_hybridSearch1 = file.read()
			enhanced_prompt = f"""
				Instructions: {instructions_hybridSearch1}
				Here are the 4 variables:
				SPEAKER: \"{supername}\"
				INPUT1: \"{user_input}\"
				SEARCH1: \"{search_response}\"
				MEMORIES1: \"{memories_response}\".
			"""			
			# print(f"\nDEBUG! from HYBRID-RESPONSE1, enhanced_prompt: {enhanced_prompt}") # PASSED!
			hybrid_response, tot_tokens1 = stm1.genContextualResp("gpt-4", enhanced_prompt, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
			update_tot_tokens1(user_id, workspace_id, platform_id, tot_tokens1)
			# print("\nDEBUG_hybrid_response: " + hybrid_response)
			custom_say(user_input, hybrid_response, user_id, channel_id, workspace_id)
			return




'''	elif is_about_Hermes(fulltext1):
		with open("./instructions/aboutHermes1.txt", "r") as file:
			instructions_aboutHermes1 = file.read()
		enhanced_prompt = f"""
			Instructions: {instructions_aboutHermes1}
			Here are the 2 variables:
			SPEAKER: \"{supername}\"
			USER_INPUT1: \"{user_input}\".
		"""
		aboutHermes_response = stm1.genContextualResp("gpt-4", enhanced_prompt, supername, user_id, channel_id, workspace_id, platform_id, timestamp, timestring)
		# print("\nDEBUG_aboutKairos_response: " + aboutKairos_response)
		custom_say(user_input, aboutHermes_response, user_id, channel_id, workspace_id)
		return'''

'''
	elif len(input_list1) == 2 and input_list1[0] == "@hermes":
		keyword = input_list1[1]
		if keyword in ["w0", "w1", "w2", "w3", "w4"]:
			vers = int(keyword[1])  # Extract the integer from the keyword
			welcome_message(user_id, channel_id, vers)
			return
'''