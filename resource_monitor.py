import threading
import time
import psutil

class ResourceMonitor(threading.Thread):
    def __init__(self, interval=0.1):
        super(ResourceMonitor, self).__init__()
        self.interval = interval
        self.running = False
        self.cpu_usage = []
        self.memory_usage = []

    def run(self):
        self.running = True
        psutil.cpu_percent(None)  # Discard the first percent reading
        while self.running:
            self.cpu_usage.append(psutil.cpu_percent(interval=None))
            self.memory_usage.append(psutil.virtual_memory().percent)
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def get_average_usage(self):
        avg_cpu = sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
        avg_memory = sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0
        return avg_cpu, avg_memory

    def clear(self):
        self.cpu_usage = []
        self.memory_usage = []
