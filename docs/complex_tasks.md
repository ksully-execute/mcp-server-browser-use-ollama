# Complex Tasks for Enhanced Ollama Integration

This repository contains a collection of complex, multi-step task prompts designed to demonstrate the full capabilities of the enhanced Ollama integration. These tasks are specifically crafted to showcase how Ollama can be used throughout an interactive process, maintaining context, adapting to new information, and providing transparent reasoning.

## Available Task Prompts

### 1. E-commerce Product Research and Competitive Analysis
- **File**: `complex_task_prompt.md`
- **Description**: A comprehensive market research task that involves navigating multiple websites, extracting product information, analyzing customer sentiment, and generating a detailed competitive analysis report.
- **Key Capabilities Demonstrated**: Context maintenance across multiple websites, information extraction and synthesis, visual content analysis, and structured reporting.

### 2. Build and Test a RESTful API with Database Integration
- **File**: `technical_task_prompt.md`
- **Description**: A technical software development task that involves building a complete RESTful API for a task management system, including database integration, authentication, testing, and documentation.
- **Key Capabilities Demonstrated**: Code generation, debugging, technical decision-making, documentation generation, and best practices implementation.

### 3. Comprehensive COVID-19 Data Analysis and Visualization
- **File**: `data_analysis_task_prompt.md`
- **Description**: A data science task that involves collecting, cleaning, analyzing, and visualizing COVID-19 data from multiple sources, creating predictive models, and generating actionable insights.
- **Key Capabilities Demonstrated**: Data processing, statistical analysis, visualization generation, model development, and insight communication.

## How to Run Complex Tasks

The `run_complex_task.py` script provides an easy way to execute these complex tasks using the enhanced Ollama integration.

### Prerequisites

1. Ensure you have Ollama installed and running:
   ```bash
   ollama serve
   ```

2. Install the required Python packages:
   ```bash
   pip install langchain_core langchain_ollama mcp
   ```

3. Make sure the enhanced client implementation is available:
   ```bash
   # The enhanced_client.py file should be in the current directory
   ls enhanced_client.py
   ```

### Usage

Run a complex task using the following command:

```bash
python run_complex_task.py <task_file> <server_script> [--model MODEL_NAME] [--debug]
```

#### Arguments:

- `task_file`: Path to the task description file (e.g., `complex_task_prompt.md`)
- `server_script`: Path to the MCP server script (e.g., `server.py`)
- `--model`: (Optional) Specify which Ollama model to use (e.g., `llama3:8b`, `qwen2.5-coder:7b`)
- `--debug`: (Optional) Enable debug logging for more detailed output

#### Examples:

```bash
# Run the e-commerce product research task
python run_complex_task.py complex_task_prompt.md server.py

# Run the technical API development task with a specific model
python run_complex_task.py technical_task_prompt.md server.py --model llama3:8b

# Run the data analysis task with debug logging
python run_complex_task.py data_analysis_task_prompt.md server.py --debug
```

## How It Works

The enhanced Ollama integration transforms how Ollama is used in browser automation and complex tasks:

1. **Interactive Feedback Loop**: Instead of making a single call at the beginning, Ollama receives feedback after each action and can adjust its strategy accordingly.

2. **Conversation Memory**: The client maintains a conversation history that includes all previous actions and results, providing Ollama with full context.

3. **Step-by-Step Reasoning**: Ollama explains its thought process before each action, making its decision-making transparent and understandable.

4. **Flexible Action Parsing**: The client can parse Ollama's responses in multiple formats, allowing for more natural expression of reasoning.

5. **Error Handling and Recovery**: The enhanced implementation includes robust error handling and recovery mechanisms.

## Customizing Tasks

You can create your own complex task prompts by following these guidelines:

1. Break the task into clear, sequential steps
2. Provide specific requirements and constraints for each step
3. Include additional requirements or considerations
4. Explain how the task demonstrates Ollama's capabilities

Save your custom task prompt as a markdown file and run it using the `run_complex_task.py` script.

## Logging and Debugging

The script generates a log file (`complex_task.log`) that captures the entire execution process. This is useful for:

- Reviewing Ollama's reasoning and decision-making
- Identifying any issues or bottlenecks
- Understanding how Ollama adapts to new information
- Analyzing the conversation flow

Use the `--debug` flag for more detailed logging.

## Performance Considerations

Complex tasks can be resource-intensive and may require:

- A powerful Ollama model (e.g., llama3:70b or qwen2.5-coder:14b)
- Sufficient system memory (at least 16GB recommended)
- Patience, as complex tasks may take time to complete

You can monitor Ollama's resource usage during task execution using tools like `htop` or `nvidia-smi` (for GPU usage).
