import os
import requests
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
# from duckduckgo_search import ddg
from duckduckgo_search import DDGS

load_dotenv()

search_engine = os.getenv("SEARCH_OPENAI_ENGINE")
max_search_results = int(os.getenv("MAX_SEARCH_RESULTS"))
max_tokens_per_result = int(os.getenv("MAX_TOKENS_PER_RESULT"))

def search_web_ddg(search_term, max_search_results=max_search_results):
    search_results = []
    search_count1 = 0
    ddg_generator = DDGS().text(search_term, safesearch="moderate", max_results=int(max_search_results))
    for result in ddg_generator:
        title = result['title']
        url = result['href']
        content = result['body'][:max_tokens_per_result]
        formatted_result = f"[{len(search_results) + 1}] {title}\n{content}\nDDGS: {url}\n"
        search_results.append(formatted_result)
        search_count1 += 1    
    print(f"Successfully fetched {search_count1} search results.")
    return search_results

def google_cse_search(search_term, api_key, cse_id, max_search_results=max_search_results):
	service = build("customsearch", "v1", developerKey=api_key)
	results_list = []

	for i in range(0, int(max_search_results)):
		results = service.cse().list(q=search_term, cx=cse_id, safe="active", start=i + 1, num=1).execute()

		if 'items' in results:
			for result in results['items']:
				title = result['title']
				url = result['link']
				content = result['snippet'][:max_tokens_per_result]
				formatted_result = f"[{i + 1}] {title}\n{content}\nGS: {url}\n"
				results_list.append(formatted_result)
		else:
			break

	return results_list

def search_web_serp_api(search_term, api_key, max_search_results=max_search_results):
	results_list = []
	for i in range(0, max_search_results, 10):
		try:
			response = requests.get(
				"https://serpapi.com/search",
				params={
					"q": search_term,
					"api_key": api_key,
					"start": i,
					"num": max_search_results,
					"source": "python",
					"engine": "google",
					"safe": "active",
				},
			)
			data = json.loads(response.text)

			if 'search_information' in data and data['search_information']['total_results'] == 0:
				break

			if "organic_results" in data:
				for index, result in enumerate(data["organic_results"]):
					if i + index >= max_search_results:
						break
					title = result["title"]
					url = result["link"]
					content = result["snippet"][:max_tokens_per_result]
					formatted_result = f"[{i + index + 1}] {title}\n{content}\nSAS: {url}\n"
					results_list.append(formatted_result)
			else:
				break
		except Exception as e:
			print(f"Error with SerpApi Key: {api_key}. Trying next set.")
			break

	return results_list

def search_web(search_term, max_search_results=max_search_results):
	api_keys = [os.getenv("GOOGLE_API_KEY_1"), os.getenv("GOOGLE_API_KEY_2")]
	cse_ids = [os.getenv("GOOGLE_CSE_ID_1"), os.getenv("GOOGLE_CSE_ID_2")]
	serp_api_keys = [os.getenv("SERP_API_KEY_1"), os.getenv("SERP_API_KEY_2")]

	results_list = []

	# Try DuckDuckGo (DDG) first
	results_list = search_web_ddg(search_term, max_search_results)

	# Try Google_Custom_Search
	if not results_list:
		for api_key, cse_id in zip(api_keys, cse_ids):
			results_list = google_cse_search(search_term, api_key, cse_id, max_search_results)
			if results_list:
				break

	# If no results from Google Custom Search, try SerpApi
	if not results_list:
		for serp_api_key in serp_api_keys:
			try:
				results_list = search_web_serp_api(search_term, serp_api_key, max_search_results)
				if results_list:
					break
			except Exception as e:
				print(f"Error with SerpApi Key: {serp_api_key}. Trying next set.")
				continue

	if not results_list:
		return "Error: All API keys and CSE_IDs failed. Please check your credentials."

	results_string = '\n'.join(results_list)
	return results_string
