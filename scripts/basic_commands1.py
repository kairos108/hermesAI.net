import os
import random
from slack_bolt import App
from dotenv import load_dotenv
load_dotenv()

bolt_app = App(token=os.getenv("SLACK_BOT_TOKEN"))
AI_name = os.getenv("AI_NAME")

def welcome_message(user_id, channel_id, vers):
	try:
		with open(f"./instructions/welcome{vers}.txt", "r") as file:
			wMessage = file.read()
		bolt_app.client.chat_postMessage(channel=channel_id, text=wMessage, unfurl_links=False)
	except FileNotFoundError:
		print(f"Error: welcome{vers}.txt not found.")
	except SlackApiError as e:
		print(f"Error posting welcome message: {e}")

def welcome_new_user(user_id, channel_id):
	if channel_id == os.getenv("WELCOME_CHANNEL"):
		wMessage = f"""
<@{user_id}> Hi there! First things first! :sweat_smile:

*DISABLE NOTIFS:*
> Configure your settings so that you wont get flooded with notifs and emails.
> 1. Click on your profile picture on the very top right of your screen.
> 2. Click "Preferences".
> 3. Click "Notifications" if you're not already there (its the first option).
> 4. Select "Direct messages, mentions, & keywords only".
> 5. In that same window/screen, scroll down to the bottom.
> 6. Uncheck "Send me email notifications for mentions and direct messages"

*INTRO:*
> I am Hermes, and I am here to be of service.
> I am an AI, coded from the ground up by Kairos, and you can ask me any questions whatsoever, just like you would a person! 
> You can speak to me in English, Chinese, Bahasa, Tamil, or whatever else you're comfortable with!

*USING HERMES:*
> In order to speak to me, you need to type in an @Hermes to mention me.
> If you don't, I will not respond to you.
> 
> You can try it later, but to talk to me, you basically type in the following:
> @Hermes <enter> your-message <enter>
> 
> Got it? Cool, we hope you have a pleasant stay here!

*MY SPECIAL ABILITIES:*
> What makes me special, is that I have both long and short term memory, and have access to live web-search.
> 
> 1. Tell me what's your favorite <whatever>, and then ask me again (much) later, even months later.
> 2. Ask me about the latest news, such as "what happened to Signature Bank?", "what happened to Sam Altman recently?", or "who's the ceo of twitter in 2023?".

*DISCLAIMER:*
> USE HERMES AT YOUR OWN RISK. 
> THIS IS JUST A PRODUCT DEMO. 
> ALL RIGHTS RESERVED. 
> COPYRIGHT 2023, KAIROS SIDDHARTHA KAIZEN/ HERMESAI.NET .
> 
> WARNING!:
> While everything is indeed fully encrypted, Hermes will forever remember whatever you said to him, and as an AI, it's best to assume that he can't discern what's sensitive, private, personal, or secret information, so please use Hermes with caution and discretion! (Example, please dont mention passwords, secrets, etc, here.)
		"""
		bolt_app.client.chat_postMessage(channel=channel_id, text=wMessage, unfurl_links=False)

def say_greetings1(fulltext1):
	if any(keyword.lower() in fulltext1.lower() for keyword in ["sup", "whats up", "what's up", "yo", "whazzup", "whassup"]):
		greetings = [
			"WHAZZAAAAAAA!!!!!",
			"Yo!",
			"Sup, what's good?",
			"Here for ya homie, what's up?",
			"All good buddy. Whaddya need?",
			"WORK WORK!",
			"Something need doing?",
			"WE'RE UNDER ATTAAACK! Oops, sorry, I've been playing too much Warcraft. Sup!"
		]
		return random.choice(greetings)
	else:
		greetings = [
			"Warm greetings, human.",
			"Well met, human.",
			"How fare thee, mortal?",
			"How may I be of service?",
			"Well met. What ails thee, mortal?",
			"NOT ENOUGH GOLD! Oops, sorry, I've been playing too much Warcraft. Hey there!"
		]
		return random.choice(greetings)