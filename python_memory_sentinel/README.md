# Python Memory Sentinel

Python Memory Sentinel is a utility for monitoring and managing running Python processes. It provides a real-time view of memory and CPU usage, allowing you to terminate or restart processes that are consuming too many resources.

The application also features a "Sentinel Rules" system, which allows you to define automated actions, such as terminating a process if it exceeds a certain memory threshold for a given duration.

## Features

- **Process Dashboard:** Lists all running Python processes with their PID, memory usage, CPU usage, and full command.
- **Real-time Graphing:** Select a process to see a live graph of its memory consumption.
- **Action Controls:** Terminate or restart any selected process.
- **Sentinel Rules:** Create custom rules to automatically manage processes based on their resource usage.

## How to Run

1.  **Prerequisites:** You need Python 3.6+ installed.

2.  **Install Dependencies:**
    Open a terminal or command prompt, navigate to this directory, and run the following command to install the required libraries:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application:**
    Once the dependencies are installed, you can start the application with this command:
    ```bash
    python3 main.py
    ```

    Note: On some Linux systems, you may need to install additional dependencies for Qt6. For Debian/Ubuntu, you can run:
    ```bash
    sudo apt-get install libxcb-cursor0 xvfb
    ```
    And then run the application with `xvfb-run python3 main.py`.
