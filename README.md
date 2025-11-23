# Example Agent

AI agent for optimizing alert configurations in a Dynatrace tenant. In the final answer you always replace the settings object id with the event.name.

## How to set up?

Following environment variables must be set:

One of the following:
* OPENAI_API_KEY=YOUR_KEY

Dynatrace
* DT_TENANT=<YOUR_DOMAIN>.live.apps.dynatrace.com
* DT_API_TOKEN=<YOUR_PLATFORM_API_TOKEN>

Configure the DT_API_TOKEN within your Dynatrace account management. Create a new platform token with the following permission scopes:
- 