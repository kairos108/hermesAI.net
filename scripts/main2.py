import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack2 import handle_slack_events
from pinecone3 import pinecone_batch_upsert_loop, pinecone_batch_upsert_loop_66
from basic_commands1 import welcome_new_user
import time
import threading

load_dotenv()
bolt_app = App(token=os.getenv("SLACK_BOT_TOKEN"))

bolt_app.event("app_mention")(handle_slack_events)
bolt_app.event("member_joined_channel")(welcome_new_user)

if __name__ == "__main__":
	while True:
		handler = SocketModeHandler(bolt_app, os.environ["SLACK_APP_TOKEN"])
		# post_to_all_channels("_(Hermes is online.)_ Hermes, at your service. Pleasure! Normally I wouldn't get mixed up with humans, but for you, I will be making an exception. Come now, we both have places to be!")

		# Create a thread to run the pinecone_batch_upsert_loop function every 3 minutes
		upsert_thread = threading.Thread(target=pinecone_batch_upsert_loop)
		upsert_thread.start()  # Start the thread

		# Checks if there are more than 99 vectors to be upserted, will trigger. Loops every 66 seconds.
		upsert_thread2 = threading.Thread(target=pinecone_batch_upsert_loop_66)
		upsert_thread2.start()  # Start the thread

		handler.start()
