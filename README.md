# FastAPI Realtime AI Use Cases

This repository contains a FastAPI application that leverages OpenAI's Realtime API, integrated with Twilio, to manage dynamic use cases. Each use case is defined within the `/usecases` directory, allowing for customized workflows for incoming calls.

## Table of Contents

- [Adding a New Use Case](#adding-a-new-use-case)
- [Webhook URL Construction](#webhook-url-construction)
- [Twilio Configuration](#twilio-configuration)

## Adding a New Use Case

To incorporate a new use case, follow these steps:

1. **Duplicate an Existing Use Case Folder via GitHub Web Interface:**
   - Navigate to the repository on GitHub.
   - Access the `/usecases/` directory.
   - Select an existing use case folder (e.g., `interview`).
   - Individually open each file within the selected folder.
   - Click the "Copy" icon to copy the file's contents.
   - Navigate back to the `/usecases/` directory.
   - Click "Add file" > "Create new file."
   - In the "Name your file..." field, enter the new folder name followed by a slash and the file name (e.g., `new_use_case/config.py`).
   - Paste the copied content into the new file.
   - Repeat this process for each file in the original use case folder.

2. **Modify `config.py`:**
   - Within the new use case folder (e.g., `/usecases/new_use_case/`), open `config.py`.
   - Update the configuration variables to align with the new use case requirements:
     - **`VOICE`**: Select an appropriate voice (e.g., 'ash', 'ballad', 'coral').
     - **`INTRO_TEXT`**: Craft an introduction message relevant to the new use case.
     - **`GREETING_TEXT`**: Define how the AI should greet the user.
     - **`SYSTEM_INSTRUCTIONS`**: Provide specific instructions tailored to the new use case.

3. **Update `prompt_variables.py`:**
   - Adjust the variables in `prompt_variables.py` to reflect the new use case context, such as:
     - Job descriptions
     - Candidate resumes
     - Interview guidelines
     - Any other pertinent prompts or data

4. **Commit Changes to the Main Branch:**
   - After making the necessary modifications, scroll to the bottom of the GitHub web interface.
   - In the "Commit changes" section, add a descriptive commit message.
   - Ensure the "Commit directly to the `main` branch" option is selected.
   - Click "Commit changes" to apply your updates.

*Note*: Changes committed to the `main` branch will trigger the CI/CD pipeline, automatically deploying the updates to the production URL.

## Webhook URL Construction

The webhook URL format is:
```
https://automobile-api-v2-645638472706.us-central1.run.app/incoming-call/{type}
```

- **`{type}`**: Corresponds to the folder name under `/usecases/` (e.g., `interview`, `new_use_case`).

*Note*: The base URL `https://automobile-api-v2-645638472706.us-central1.run.app` is the actual endpoint for this application.

## Twilio Configuration

To route incoming calls to your specific use case webhook:

1. **Access Twilio Console:**
   - Log into your [Twilio Console](https://www.twilio.com/console).
   - Navigate to **Phone Numbers** > **Manage** > **Active Numbers**.

2. **Select a Phone Number:**
   - Click on the phone number you wish to configure.

3. **Configure Voice Settings:**
   - Under the **Voice & Fax** section:
     - Set **A Call Comes In** to **Webhook**.
     - Enter your webhook URL in the format:
       ```
       https://automobile-api-v2-645638472706.us-central1.run.app/incoming-call/{type}
       ```
       Replace `{type}` with your use case folder name (e.g., `new_use_case`).

4. **Save Changes:**
   - Click **Save** to apply the new settings.

For detailed instructions, refer to Twilio's official documentation on [Configuring Webhooks for Incoming Calls](https://www.twilio.com/docs/voice/tutorials/how-to-respond-to-incoming-phone-calls-node-js#configure-your-webhook-url).

*Note*: Ensure your webhook URL is publicly accessible and uses HTTPS for secure communication.




* common
type: str = "rag", // "api"
intermediate: bool = False, // True
* rag
db: str = "pg", // "faiss"
re_rank: bool = False,
hybrid_search: bool = False,
hybrid_search_weight: float = 0.5,
top_k: int = 10,
* api
enable_fields: bool = False,
context_limit: int = 6000, 