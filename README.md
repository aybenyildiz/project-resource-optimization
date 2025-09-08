# project-resource-optimization
This project is a web-based decision support system that creates the most efficient and balanced work plan in environments with multiple projects and limited resources. Using mathematical optimization techniques, it helps project managers minimize resource conflicts, project delays, and cost overruns.
Project Resource Optimization Tool
1. About the Project
This project is a web-based decision support system that creates the most efficient and balanced work plan in environments with multiple projects and limited resources. Using mathematical optimization techniques, it helps project managers minimize resource conflicts, project delays, and cost overruns.

2. Features
Dynamic Data Entry: Define projects, activities, resources, and precedences (dependencies) through a user-friendly interface.

Flexible Parameters: Set detailed parameters for each activity, such as minimum/maximum durations, lateness penalties, and target finish dates.

Powerful Optimization Engine: Finds the optimal plan using Mixed-Integer Linear Programming (MILP).

Advanced Visualization:

View the optimized project schedule with an interactive Gantt Chart.

Analyze the distribution of resources over time with Resource Usage Charts.

Asynchronous Architecture: Runs long optimization tasks in the background using Celery, keeping the user interface fluid.

3. Technology Stack
Backend: Python, Flask, Celery, PuLP (Optimization), SQLite

Frontend: HTML, Tailwind CSS, Chart.js, JavaScript (Fetch API)

4. Project Structure
.
├── .gitignore          # Specifies intentionally untracked files to ignore
├── README.md           # This file: Project overview and setup instructions
├── api.py              # Flask server: Handles API requests and serves the frontend
├── celery_worker.py    # Celery worker: Runs optimization tasks in the background
├── index.html          # Frontend: The user interface for the application
├── optimization_core.py# The core mathematical optimization model logic
└── requirements.txt    # Lists all necessary Python libraries for the project

5. Setup and Execution
Follow the steps below to run this project on your local machine.

Step 1: Clone the Project
Download the project as a ZIP file and extract it, or clone it using Git:

git clone <repository_url>

Step 2: Create and Activate a Virtual Environment
Create a virtual environment (venv) to keep the project's libraries isolated from your other projects.

# Run this command inside the project folder
python -m venv venv

# Activate the virtual environment
# For Windows:
.\venv\Scripts\activate
# For macOS / Linux:
source venv/bin/activate

You should see (venv) at the beginning of your terminal command line.

Step 3: Install Required Libraries
Install all necessary Python libraries with a single command:

pip install -r requirements.txt

Step 4: Start the System (2 Separate Terminals Required)
The project requires two services to run simultaneously. For this, open two separate terminal windows.

Terminal 1: Start the Celery Worker

This terminal runs the "worker" that will perform the optimization calculations in the background.

# Run this command while (venv) is active
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo

You will see a message indicating that the worker is ready to accept tasks.

Terminal 2: Start the API Server

This terminal runs the server that will serve the web interface and receive optimization requests.

# Run this command while (venv) is active
python api.py

When the server starts, you will see a message like Running on http://0.0.0.0:5000.

Step 5: Open the Application in Your Browser
Everything is ready! Open your web browser and navigate to the following address:

http://127.0.0.1:5000

The application interface will appear. You can now start using the project.
