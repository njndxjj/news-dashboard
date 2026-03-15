# Director Workflow

## File: `director_workflow.py`

### Description
This script orchestrates the complete workflow for generating a newspaper-style report from fetched and processed news data. It invokes the individual agent scripts in sequence and ensures a seamless execution pipeline.

### Workflow Steps
1. **Collector:**
   - Executes the `fetch_rss.py` script to gather news from RSS feeds.
   - Output: `aggregated_news.json` file.

2. **Processor:**
   - Executes the `analyze_news.py` script to analyze and classify the news data.
   - Output: `news_analysis.db` SQLite database.

3. **Presenter:**
   - Executes the `render_newspaper.py` script to render a newspaper-style long image.
   - Output: `newspaper_theme.png` file.

### Running the Workflow
To execute the complete workflow, run the following command:
```bash
python3 director_workflow.py
```

### Output
1. **News Data JSON Output:** `output/aggregated_news.json`
2. **Processed Analysis Data:** `output/news_analysis.db`
3. **Final Newspaper Image:** `output/newspaper_theme.png`

### Error Handling
- The script checks the return codes of each step and will stop the workflow if any step fails.
- Relevant logs for each step (stdout and stderr) will be displayed in the console.