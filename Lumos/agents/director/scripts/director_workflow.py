import os
import subprocess

def run_collector():
    print("Starting Collector...")
    with open("director_workflow.log", "a") as log_file:
        log_file.write("Collector started.\n")
    result = subprocess.run(["python3", "/Users/bs-00008898/OpenClaw_Data/workspace/skills/news-summary/fetch_rss.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Collector failed:", result.stderr)
        with open("director_workflow.log", "a") as log_file:
            log_file.write(f"Collector failed: {result.stderr}\n")
        return False
    return True

def run_processor():
    print("Starting Processor...")
    result = subprocess.run(["python3", "agents/processor/scripts/analyze_news.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Processor failed:", result.stderr)
        return False
    return True

def run_presenter():
    print("Starting Presenter...")
    result = subprocess.run(["python3", "/Users/bs-00008898/OpenClaw_Data/workspace/skills/newspaper-brief/render_newspaper.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("Presenter failed:", result.stderr)
        return False
    return True

def main():
    print("Director workflow initiated.")

    # Step 1: Collect data
    if not run_collector():
        print("Workflow aborted: Collector step failed.")
        return

    # Step 2: Process data
    if not run_processor():
        print("Workflow aborted: Processor step failed.")
        return

    # Step 3: Present results
    if not run_presenter():
        print("Workflow aborted: Presenter step failed.")
        return

    print("Workflow completed successfully! The report is ready.")

if __name__ == "__main__":
    main()