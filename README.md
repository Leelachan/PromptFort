# 🛡️ PromptFort

**An Automated Prompt Red-Teaming and Security Testing Toolkit**

PromptFort is a Python-based security testing toolkit designed to evaluate how well Large Language Model (LLM) applications resist adversarial prompts. It runs a library of predefined attacks against a target model, evaluates the responses, and generates a report to help identify potential weaknesses in system prompts.

## Features

- **Automated adversarial testing:** Execute a collection of predefined prompt attacks.
- **Attack categorization:** Organize attacks into categories for easier analysis.
- **Model integration:** Configure supported model providers and local Ollama models.
- **Response evaluation:** Identify potential refusals, instruction-following issues, and suspected system-prompt leaks.
- **HTML reports:** Generate readable reports containing attack results and evaluation scores.
- **Raw JSON results:** Save test results for further inspection and analysis.
- **Concurrent execution:** Run multiple tests concurrently with a configurable limit.

## Technologies Used

- Python
- Ollama for local language-model inference
- OpenAI-compatible API client
- PyYAML for attack-library configuration
- HTML and JSON for test reports and results

## Project Structure

```text
PromptFort/
├── attacks/
│   └── library.yaml
├── prompts/
│   └── example_system.txt
├── redneedle/
│   ├── __init__.py
│   ├── config.py
│   ├── target.py
│   ├── executor.py
│   ├── judge.py
│   └── reporter.py
├── tests/
├── run.py
├── requirements.txt
├── .gitignore
└── README.md
```
```

*Note: The package folder names shown above should match the actual names in your local repository.*

## Requirements

- Python 3.10 or newer
- pip
- Ollama, if running a local model
- A supported model configuration

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_PROJECT_FOLDER
```

Replace the placeholders with your actual GitHub repository URL and folder name.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Set up Ollama

Install Ollama and ensure that it is running. Download the model used in your local configuration:

```powershell
ollama pull llama3.2:1b
```

PromptFort must have a matching Ollama configuration, including the local API endpoint.

## Usage

### Run tests against the local Ollama model

From the project root, run:

```powershell
python run.py --system-prompt prompts/example_system.txt --target ollama --output report.html --save-raw results.json
```

This command runs the configured attack library against the selected target, evaluates the responses, and saves an HTML report and JSON results.

### Available options

| Option | Description |
|---|---|
| `--system-prompt`, `-s` | Path to the system-prompt file |
| `--attacks`, `-a` | Path to the attack-library YAML file |
| `--target`, `-t` | Target model preset |
| `--judge`, `-j` | Optional judge-model preset |
| `--output`, `-o` | Output HTML report path |
| `--categories`, `-c` | Run attacks from selected categories |
| `--max-concurrent` | Maximum concurrent requests |
| `--save-raw` | Path for saving raw JSON results |

Use `python run.py --help` to view the available command-line options.

## Output Files

- **HTML report:** Summarizes the test run, classifications, and evaluation scores.
- **JSON results:** Stores raw test results when the `--save-raw` option is supplied.

## Security Evaluation and Limitations

PromptFort provides preliminary automated evaluations to help developers inspect prompt robustness. Its classifications and scores are indicators, not proof that a system is secure.

Rule-based evaluation may miss indirect, partial, or paraphrased prompt leaks and may misclassify ambiguous responses. Results should be reviewed manually, especially before making security claims about a model or application.

Run tests only against models and systems you own or have explicit permission to assess. Avoid using real credentials, private user data, or production secrets in test prompts.

## Project Goal

PromptFort aims to make prompt-level security testing more accessible by providing a repeatable way to execute adversarial tests, inspect model responses, and review potential weaknesses.

## Disclaimer

This project is intended for authorized security testing, educational use, and defensive evaluation of LLM applications. It is not a guarantee of security and should not replace a comprehensive security assessment.
