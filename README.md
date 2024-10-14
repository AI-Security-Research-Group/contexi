<h1 align="center"> CONTEXI <img src="https://www.svgrepo.com/show/507046/cha-rect-swear.svg" width="28"> </h1> <br>
<table align="center">
<tr>
<td>
Contexi let you interact with entire codebase or data with context using a local LLM on your system.
</td>
</tr>
</table>

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/aqua.png)

Contexi uses: <br> 
- Multi Prompt Contextually Guided Retrieval-Augmented Generation <br>
- Self-Critique & Self-Corrective using [Chain-of-Thoughts](https://arxiv.org/abs/2201.11903) <br>
- Document [Re-Ranking](https://developer.nvidia.com/blog/enhancing-rag-pipelines-with-re-ranking/)

techniques to provide the most relevant context-aware responses to questions about your data. 


## Key Features <img src="https://media.giphy.com/media/VgCDAzcKvsR6OM0uWg/giphy.gif" width="40">

✅ Analyzes and understands your entire codebase and data, not just isolated code snippets. <br>
✅ Answers questions about potential security vulnerabilities anywhere in the code. <br>
✅ Import code using git url for analysis. <br>
✅ Learns from follow-up questions and continuously answers based on chat history context <br>
✅ Runs entirely on your local machine for free, **No Internet is required**. <br>


## Web UI <img src="https://www.svgrepo.com/show/343850/blog-seo-optimization-search.svg" width="25"> 
<img width="850" alt="Screenshot 2024-10-01 at 11 34 06 PM" src="https://github.com/user-attachments/assets/58598159-7c11-40ef-895e-0b44a2eef50e">


## How it works? <img src="https://www.svgrepo.com/show/530592/creativity.svg" width="20"> 

🚀 [Get started with Wiki](https://github.com/AI-Security-Research-Group/Contexi/wiki) <br>
<img src="https://www.svgrepo.com/show/533373/diagram-subtask.svg" width="15"> [Sequence Diagram](https://github.com/user-attachments/assets/b7c32d6a-c825-4058-a651-33075b7c541c) 


## Pre-requisites <img src="https://www.svgrepo.com/show/530571/conversation.svg" width="25"> 

* [Ollama](https://ollama.ai/) - Preferred models: [qwen2.5](https://ollama.com/library/qwen2.5) (for more precise results)
* Recommended 16 GB RAM and plenty of free disk space
* Python 3.7+
* Various Python dependencies (see `requirements.txt`)

## Supported Programming Languege/Data: <img src="https://www.svgrepo.com/show/507050/cha-translate-2.svg" width="25"> 
- Tested in Java codebase (You can configure ```config.yml``` to load other code/file formats)

## Installation <img src="https://www.svgrepo.com/show/530572/accelerate.svg" width="25"> 

**We'd recommend installing app on [python virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/)**

1. Clone this repository:
   ```
   git clone https://github.com/AI-Security-Research-Group/Contexi.git
   cd Contexi
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Edit ```config.yml``` parameters based on your requirements.

4. Run
   ```
   python3 main.py
   ```

## Usage <img src="https://media.giphy.com/media/WUlplcMpOCEmTGBtBW/giphy.gif" width="30">
Upon running main.py just select any of the below options:

```
(venv) coder@system ~/home/Contexi $

Welcome to Contexi!
Please select a mode to run:
1. Interactive session
2. UI
3. API
Enter your choice (1, 2, or 3): 
```

You are ready to use the magic stick. 🪄

### API Mode

Send POST requests to `http://localhost:8000/ask` with your questions.

Example using curl:

```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "What is the purpose of the Login class?"}'
```

Response format:

```json
{
  "answer": "The Login class is responsible for handling user authentication..."
}
```

Open an Issue if you're having problem with running or installing this script. (Script is tested in mac environment.)

### Customization <img src="https://www.svgrepo.com/show/530579/set-up.svg" width="25"> 
You can customize various aspects of the script:
- Adjust the `chunk_size` and `chunk_overlap` in the `split_documents_into_chunks` function to change how documents are split.
- Modify the `PROMPT_TEMPLATE` to alter how the LLM interprets queries and generates responses.
- Change the `max_iterations` in `perform_crag` to adjust how many times the system will attempt to refine an answer.
- Modify the `num_ctx` in `initialize_llm` to adjust the llm context window for better results.
- Adjust ```n_ideas``` parameter to define the depth of accuracy and completeness you need in the answers.

## Troubleshooting
- If you encounter memory issues, try reducing the `chunk_size` and `num_ctx` or the number of documents processed at once.
- Ensure that Ollama is running and the correct model name is mentioned in ```config.yml``` file.

## Use Cases

- **Codebase Analysis**: Understand and explore large code repositories by asking natural language questions.
- **Security Auditing**: Identify potential security vulnerabilities by querying specific endpoints or functions.
- **Educational Tools**: Help new developers understand codebases by providing detailed answers to their questions.
- **Documentation Generation**: Generate explanations or documentation for code segments. AND MORE..

### To-Do List for Contributors

- [ ] ~~Make the important parameters configurable using yaml file~~ ✅<br>
- [ ] Drag and drop folder in UI for analysis <br>
- [ ] Scan source folder and suggest file extension to be analyzed <br>
- [ ] Make config.yml configurable in UI <br>
- [ ] Session based chat to switch context on each new session <br>
- [ ] Persistant chat UI interface upon page refresh <br>
- [ ] Add only most recent response in history context <br>
- [ ] ~~Implement tree-of-thoughts concept~~ <br>
- [ ] ~~Create web interface~~ ✅
- [ ] ~~Integrate the repository import feature which imports repo locally automatically to perform analysis~~ ✅

### Security Workflow (To-Do)

- [ ] Use Semgrep to identify potential vulnerabilities based on patterns.
- [ ] Pass the identified snippets to a data flow analysis tool to determine if the input is user-controlled.
- [ ] Provide the LLM with the code snippet, data flow information, and any relevant AST representations.
- [ ] Ask the LLM to assess the risk based on this enriched context.
- [ ] Use the LLM's output to prioritize vulnerabilities, focusing on those where user input reaches dangerous functions.
- [ ] Optionally, perform dynamic analysis or manual code review on high-risk findings to confirm exploitability.

## Contributing

Contributions to Contexi are welcome! Please submit pull requests or open issues on the GitHub repository.

## Acknowledgments

- This project uses [Ollama](https://ollama.ai/) for local LLM inference.
- Built with [LangChain](https://python.langchain.com/), [Streamlit](https://streamlit.io/) and [FastAPI](https://fastapi.tiangolo.com/).
