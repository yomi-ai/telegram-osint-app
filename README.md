# Telegram Based App For OSINT

![healthchecks.io](https://healthchecks.io/badge/949d5bcd-bbfb-4d3c-9cca-cb43cf/6Qx1bGGj-2.svg)

This is a Python application designed for Open Source Intelligence (OSINT) that leverages Telegram channels to collect, process, and analyze data. The application uses the **PyNest** framework for modularity and dependency injection, and integrates with the OpenAI API for advanced processing.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Application](#running-the-application)
- [Project Structure](#project-structure)
- [Usage](#usage)

## Features

- Connects to specified Telegram channels to read messages.
- Processes messages using OpenAI's GPT models.
- Modular architecture using the PyNest framework.
- Configurable through environment variables.
- Background job for continuous data fetching and processing.

## Prerequisites

- **Python 3.10** or higher
- **Poetry** for dependency management
- **Telegram API credentials**:
  - API ID
  - API Hash
- **OpenAI API key**

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/telegram-osint-app.git
   cd telegram-osint-app
    ```

2. **Install dependencies**

Ensure you have Poetry installed. If not, install it using:

```bash
pip install poetry
```

Then, install the project dependencies:

```bash
poetry install
```

### Environment Variables

The application requires certain environment variables to be set for configuration. You can create a `.env` file in the root directory of the project to set these variables.

### Required Environment Variables

- **OPENAI_API_KEY**: Your OpenAI API key.
- **API_ID**: Your Telegram API ID.
- **API_HASH**: Your Telegram API Hash.
- **TARGET_CHANNEL**: The Telegram channel where processed messages will be sent.
- **MODEL_NAME**: The name of the OpenAI model to use (e.g., `gpt-4`).

### Example `.env` File

Create a file named `.env` in the root directory and add the following:

```env
OPENAI_API_KEY=your-openai-api-key

API_ID=your-telegram-api-id
API_HASH=your-telegram-api-hash

TARGET_CHANNEL=@yourtargetchannel
MODEL_NAME=gpt-4
```

Note: Replace the placeholder values (your-openai-api-key, your-telegram-api-id, etc.) with your actual credentials.

## Running the Application

### Running Locally

You can run the application locally using the following command:

```bash
poetry run python main.py
```

This will start the application on [http://0.0.0.0:8000](http://0.0.0.0:8000).

---

## Using Docker

Alternatively, you can run the application inside a Docker container.

### Build the Docker Image

```bash
docker build -t telegram-osint-app:latest .
```

## Run the Docker Container
```bash
docker run -p 8000:8000 --env-file .env telegram-osint-app:latest
```

Note: Make sure your .env file is in the root directory and contains all the necessary environment variables.

## Project Structure

The project follows a modular architecture provided by the **PyNest** framework. Here's an overview of the main components:

- **`main.py`**: Entry point of the application.
- **`src/`**: Contains the application source code.
  - **`app_module.py`**: Defines the main application module.
  - **`app_controller.py`**: Handles HTTP routes.
  - **`app_service.py`**: Contains business logic.
  - **`providers/`**: Contains all the service providers.
    - **`config/`**: Configuration services.
    - **`logger/`**: Logging services.
    - **`telegram/`**: Telegram integration services.
    - **`openai/`**: OpenAI integration services.
    - **`cost_calculator/`**: Services for calculating costs.
  - **`jobs/`**: Background jobs (e.g., `osint_job.py`).

---

## Usage

The application continuously fetches messages from specified Telegram channels, processes them (e.g., translates or filters important messages), and sends the processed messages to a target Telegram channel.
