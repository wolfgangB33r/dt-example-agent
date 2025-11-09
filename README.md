# Alert Optimizer Agent

AI agent for optimizing alert configurations in a Dynatrace tenant. In the final answer you always replace the settings object id with the event.name.

## How to set up?

The agent is designed to run as a scheduled, autonomous job that can be deployed in a dockerized job runtime environment
such as Google Cloud Run Job.

Following environment variables must be set:

One of the following:
* OPENAI_API_KEY=YOUR_KEY
* GOOGLE_API_KEY=YOUr_KEY
Selection of the model to use:
* LLM_MODEL=google

Dynatrace
* DT_SETTINGS_API_URL=https://<YOUR_DOMAIN>.live.dynatrace.com/api/v2/settings/objects/
* DT_SETTINGS_API_KEY=<YOUR_API_TOKEN>
* DT_DQL_API_URL=https://<YOUR_DOMAIN>.live.apps.dynatrace.com/platform/storage/query/v1/query:execute?enrich=metric-metadata
* DT_DQL_API_KEY=<YOUR_PLATFORM_API_TOKEN>
