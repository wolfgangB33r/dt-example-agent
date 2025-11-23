# Helsinki - An Example Dynatrace Agent

AI agent for analyzing and optimizing alert configurations in a Dynatrace tenant.

## How to set up?

Following environment variables must be set:

**OpenAI**
* OPENAI_API_KEY=<YOUR_OWN_OPENAI_API_KEY>

**Dynatrace**
* DT_TENANT=<YOUR_DOMAIN>.live.apps.dynatrace.com
* DT_API_TOKEN=<YOUR_PLATFORM_API_TOKEN>


Configure the DT_API_TOKEN within your Dynatrace account management. Create a new platform token with the following permission scopes.
* mcp-gateway:servers:invoke
* mcp-gateway:servers:read
for reading records from Grail storage:
* storage:buckets:read
* storage:events:read
* storage:metrics:read
* storage:logs:read
* storage:entities:read

for triggering data analysis tools:
* davis:analyzers:read
* davis:analyzers:execute

for the Dynatrace Generative tools:
* davis-copilot:conversations:execute
* davis-copilot:nl2dql:execute
* davis-copilot:dql2nl:execute
* davis-copilot:document-search:execute