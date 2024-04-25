import time
import requests
from multiprocessing import Pool
import logging
import psutil
import prompts
from resource_monitor import ResourceMonitor

# Configuration for the test environment
BASE_URL = "http://localhost:1234/v1"
MODEL = "local-model"

logging.basicConfig(filename='model_test_logs.txt', level=logging.INFO, format='%(asctime)s %(message)s')

def generate_random_prompt(size):
    if size == 'very large':
        with open('book.txt', 'r', encoding='utf-8') as file:
            text = file.read().split()
            return ' '.join(text[:1000])  # Example: First 1000 words
    elif size == 'very small':
        return "Quick example."

def generate_prompt(size):
    if size == 'small':
        return prompts.SHORT_PROMPT
    elif size == 'medium':
        return prompts.MEDIUM_PROMPT
    elif size == 'large':
        return prompts.LARGE_PROMPT
    elif size == 'very large':
        with open('book.txt', 'r', encoding='utf-8') as file:
            text = file.read().split()
        return ' '.join(text[:1000]) 
    elif size == 'very small':
        return "Quick example."

def generate_response_size(size):
    token_sizes = {'small': 64, 'medium': 256, 'large': 512}
    return token_sizes[size]

def simulate_user_interaction(prompt_size, response_size):
    monitor = ResourceMonitor()
    monitor.start()  # Start monitoring

    prompt = generate_prompt(prompt_size)
    max_tokens = generate_response_size(response_size)
    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Answer within token limit."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
    )
    response_time = time.time() - start_time
    monitor.stop()  # Stop monitoring
    monitor.join()  # Wait for the thread to finish
    avg_cpu, avg_memory = monitor.get_average_usage()

    logging.info(f"Test {prompt_size}-{response_size} ran with response time {response_time:.2f}s, CPU: {avg_cpu}%, Memory: {avg_memory}%, Response: {response.text}")
    return {
        'response_time': response_time,
        'response_text': response.text,
        'cpu_usage': avg_cpu,   
        'memory_usage': avg_memory,
        'success': response.ok,
    }

def stress_tests():
    test_prompts = ['very large', 'very small']
    for size in test_prompts:
        prompt = generate_random_prompt(size)
        response_size = generate_response_size('small') 
        result = simulate_user_interaction(size, 'small')
        analyze_results([result], prompt, response_size, stress=True)

def run_tests():
    sizes = ['small', 'medium', 'large']
    combinations = [(a, b) for a in sizes for b in sizes]
    for prompt_size, response_size in combinations:
        print(f"{prompt_size} {response_size}")
        combination_results = []  # List to hold results for current combination
        for _ in range(3):  # repeat each test 3 times
            combination_results.append(simulate_user_interaction(prompt_size, response_size))
        analyze_results(combination_results, prompt_size, response_size)  # Analyze results for the current combination

def analyze_results(results, prompt_size, response_size, stress=False):
    success_rate = sum(1 for result in results if result['success']) / len(results)
    average_response_time = sum(result['response_time'] for result in results if result['success']) / sum(1 for result in results if result['success'])
    average_cpu_usage = sum(result['cpu_usage'] for result in results) / len(results)
    average_memory_usage = sum(result['memory_usage'] for result in results) / len(results)
    if stress:
        logging.info(f"Stress Test Results {prompt_size}-{response_size} - Success Rate: {success_rate*100}%, Average Response Time: {average_response_time:.2f}s, CPU Usage: {average_cpu_usage}%, Memory Usage: {average_memory_usage}%\n\n\n")
    else:
        logging.info(f"Combination {prompt_size}-{response_size} Success Rate: {success_rate*100}%, Average Response Time: {average_response_time:.2f}s, CPU Usage: {average_cpu_usage}%, Memory Usage: {average_memory_usage}%\n\n\n")

if __name__ == "__main__":
    test_type = input("Enter the test type (normal/stress): ").lower()
    if test_type == 'normal':
        run_tests()
    elif test_type == 'stress':
        stress_tests()
