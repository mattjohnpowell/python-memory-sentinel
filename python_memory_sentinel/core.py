import psutil

def get_monitored_processes():
    """
    Generator that yields information about running Python and Node.js processes.
    """
    process_names = {'python.exe', 'pythonw.exe', 'python', 'python3', 'node.exe', 'node'}
    for process in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'cmdline']):
        try:
            if process.info['name'].lower() in process_names:
                # Get memory usage in MB
                memory_mb = process.info['memory_info'].rss / (1024 * 1024)
                # Get full command line path
                cmdline = ' '.join(process.info['cmdline'])

                yield {
                    'pid': process.info['pid'],
                    'memory_mb': f"{memory_mb:.2f}",
                    'cpu_percent': process.info['cpu_percent'],
                    'cmdline': cmdline
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def main():
    """
    Main function to display information about running monitored processes.
    """
    print("Running Monitored Processes (Python and Node.js):")
    print("-" * 50)

    processes = list(get_monitored_processes())

    if not processes:
        print("No monitored processes found.")
        return

    # Find the maximum width for each column to format the output nicely
    max_pid_len = max(len(str(p['pid'])) for p in processes) if processes else 4
    max_mem_len = max(len(p['memory_mb']) for p in processes) if processes else 10
    max_cpu_len = max(len(str(p['cpu_percent'])) for p in processes) if processes else 10

    # Header
    print(f"{'PID':<{max_pid_len}} | {'Memory (MB)':<{max_mem_len}} | {'CPU (%)':<{max_cpu_len}} | {'Command Line'}")
    print("-" * (max_pid_len + max_mem_len + max_cpu_len + 15))

    for p in processes:
        print(f"{p['pid']:<{max_pid_len}} | {p['memory_mb']:<{max_mem_len}} | {p['cpu_percent']:<{max_cpu_len}} | {p['cmdline']}")

if __name__ == "__main__":
    main()
