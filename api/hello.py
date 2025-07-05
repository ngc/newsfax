from tavily import TavilyClient

# make a call 
# LLM to get list of facts
# LLM queries Tavily
# Tavily will return a list of 
# use SQL Lite 
# False, True, Somewhat True : With the sentence
def main():
    print("Hello from api!")
    parse_content_from_url_news()


def parse_content_from_url_news():

    url = "https://www.cbc.ca/news/canada/first-person-refugee-small-town-canada-1.7571127"
    tavily_client = TavilyClient(api_key="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")
    response = tavily_client.crawl(url, instructions="Find news content")
    print(response)

    

if __name__ == "__main__":
    main()
