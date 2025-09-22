
from urllib.parse import urlparse
from datetime import datetime, timezone
from langsmith import Client

url = "https://smith.langchain.com/public/8ae14960-930a-4613-a4bf-9891cc8b57a6/r"
share_token = url.rstrip("/").split("/")[-2]  # "8ae14960-930a-4613-a4bf-9891cc8b57a6"

c = Client()  # uses LANGCHAIN_API_KEY / LANGCHAIN_ENDPOINT
run = c.read_shared_run(share_token)       # returns the real Run object (with .id)
c.update_run(run.id, end_time=datetime.now(timezone.utc), error="Force-closed from API")
print("Closed:", run.id)