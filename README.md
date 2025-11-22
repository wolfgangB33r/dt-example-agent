# Example Agent

AI agent for optimizing alert configurations in a Dynatrace tenant. In the final answer you always replace the settings object id with the event.name.

## How to set up?

Following environment variables must be set:

One of the following:
* OPENAI_API_KEY=YOUR_KEY
* GOOGLE_API_KEY=YOUr_KEY

Dynatrace
* DT_SETTINGS_API_URL=https://<YOUR_DOMAIN>.live.dynatrace.com/api/v2/settings/objects/
* DT_SETTINGS_API_KEY=<YOUR_API_TOKEN>
* DT_DQL_API_URL=https://<YOUR_DOMAIN>.live.apps.dynatrace.com/platform/storage/query/v1/query:execute?enrich=metric-metadata
* DT_DQL_API_KEY=<YOUR_PLATFORM_API_TOKEN>
