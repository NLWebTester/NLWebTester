# NLWebTester

**NLWebTester** is a novel approach that uses multimodal large language models and enables low-code GUI testing. Going from natural language descriptions to executable test scripts we raise the abstraction level of testing, while at the same time we make testing more accessible and robust compared to traditional script-based methods.

## Overview

NLWebTester leverages the power of large language models (LLMs), specifically Google's Gemini, to understand user requests expressed in natural language and translate them into a series of actions that automate web browsing GUI tasks.

It utilizes Selenium for browser control and interaction, offering a seamless way to automate complex workflows within a web browser environment.

![Workflow](/demos/workflow_v2.png)

## Prerequisites

Before using NLWebTester, you need to obtain an API key from Google for the Gemini API. You can get a key by following these steps:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and click on "Get an API key".
2. [Set the secret key as an environment variables in your system](https://www3.ntu.edu.sg/home/ehchua/programming/howto/Environment_Variables.html).

**Setting the API Key in `.env` during development:**

You can set the API key in a `.env` file in the project repository:

```bash
GOOGLE_API_KEY=YOUR_API_KEY
```

You can check if the key is configured by typing `echo $GOOGLE_API_KEY` in your shell.


## Usage

To use NLWebTester, you can provide a natural language query describing the task you want to automate. NLWebTester will then interact with the agent (Gemini) to interpret the query and generate a sequence of actions to be executed by the Selenium WebDriver.

**Example 1: Login case:**

![Login case](/demos/login.png)
> NLWebTester "Open the URLs website. Write the username 'Heath93' and write the password 'xxx'. Click on the Sign In button"



## Development

NLWebTester's development workflow is managed using Pyinvoke. The `tasks/` folder contains various tasks for managing the project:

- **checks.py:** Tasks for code quality checks (linting, type checking, testing, security).
- **cleans.py:** Tasks for cleaning up build artifacts and caches.
- **containers.py:** Tasks for building and running Docker containers.
- **docs.py:** Tasks for generating and serving API documentation.
- **formats.py:** Tasks for code formatting.
- **installs.py:** Tasks for installing dependencies and pre-commit hooks.
- **packages.py:** Tasks for building and publishing Python packages.
- **publishes.py:** Tasks for publishing artifacts on software repositories.

## License

NLWebTester is licensed under the MIT License. See the [LICENSE](LICENCE.txt) file for more details.
