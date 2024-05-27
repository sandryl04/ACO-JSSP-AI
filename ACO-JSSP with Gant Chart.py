import numpy as np
import random
import matplotlib.pyplot as plt

def get_user_input():
    num_jobs = int(input("Enter the number of projects: "))
    jobs = []
    for i in range(num_jobs):
        num_tasks = int(input(f"Enter the number of activities for project {i}: "))
        job = []
        for j in range(num_tasks):
            machine = int(input(f"Enter the team number for project {i}, activity {j}: "))
            duration = int(input(f"Enter the duration for project {i}, activity {j}: "))
            job.append((machine, duration))
        jobs.append(job)
    return jobs

# Get user input for jobs, machines, and durations
jobs = get_user_input()

num_jobs = len(jobs)
num_machines = max(machine for job in jobs for machine, _ in job) + 1
pheromone_initial = 0.1
alpha = 1.0  # Pheromone importance
beta = 2.0   # Heuristic importance
evaporation_rate = 0.5
num_ants = 10
num_iterations = 100

# Initialize pheromone matrix
pheromone = np.full((num_jobs, len(jobs[0]), num_jobs, len(jobs[0])), pheromone_initial)

# Define a function to calculate the makespan of a solution
def calculate_makespan(solution):
    machine_times = np.zeros(num_machines)
    job_end_times = np.zeros(num_jobs)
    task_end_times = {(job, task): 0 for job in range(num_jobs) for task in range(len(jobs[job]))}

    for job, task in solution:
        machine, duration = jobs[job][task]
        start_time = max(machine_times[machine], task_end_times[(job, task - 1)] if task > 0 else 0)
        end_time = start_time + duration
        machine_times[machine] = end_time
        task_end_times[(job, task)] = end_time
        job_end_times[job] = end_time

    return max(job_end_times)

# Define a function to update pheromone levels
def update_pheromone(trails, solutions):
    for i in range(num_jobs):
        for j in range(len(jobs[i])):
            for k in range(num_jobs):
                for l in range(len(jobs[k])):
                    pheromone[i][j][k][l] *= (1 - evaporation_rate)
    for solution in solutions:
        makespan = calculate_makespan(solution)
        for job, task in solution:
            pheromone[job][task][job][task] += 1 / makespan

# Define a function for ant solution construction
def construct_solution():
    solution = []
    remaining_tasks = [(job, task) for job in range(num_jobs) for task in range(len(jobs[job]))]
    task_end_times = {(job, task): 0 for job in range(num_jobs) for task in range(len(jobs[job]))}
    machine_times = np.zeros(num_machines)

    while remaining_tasks:
        available_tasks = [(job, task) for job, task in remaining_tasks if task == 0 or (job, task - 1) not in remaining_tasks]
        heuristic_info = [(pheromone[job][task][job][task] ** alpha) * ((1 / (machine_times[jobs[job][task][0]] + jobs[job][task][1])) ** beta) for job, task in available_tasks]
        probabilities = np.array(heuristic_info) / np.sum(heuristic_info)
        selected_index = np.random.choice(len(available_tasks), p=probabilities)
        selected_job, selected_task = available_tasks[selected_index]
        solution.append((selected_job, selected_task))
        remaining_tasks.remove((selected_job, selected_task))
        machine_times[jobs[selected_job][selected_task][0]] += jobs[selected_job][selected_task][1]

    return solution

# Main ACO loop
best_solution = None
best_makespan = float('inf')

for iteration in range(num_iterations):
    solutions = []
    for ant in range(num_ants):
        solution = construct_solution()
        solutions.append(solution)
    update_pheromone(pheromone, solutions)
    
    current_best_solution = min(solutions, key=calculate_makespan)
    current_best_makespan = calculate_makespan(current_best_solution)
    
    if current_best_makespan < best_makespan:
        best_solution = current_best_solution
        best_makespan = current_best_makespan

print("Best solution:", best_solution)
print("Best makespan:", best_makespan)

# Generate Gantt chart
def generate_gantt_chart(solution):
    fig, ax = plt.subplots()
    machine_times = np.zeros(num_machines)
    task_end_times = {(job, task): 0 for job in range(num_jobs) for task in range(len(jobs[job]))}
    colors = plt.cm.rainbow(np.linspace(0, 1, num_jobs))

    for job, task in solution:
        machine, duration = jobs[job][task]
        start_time = max(machine_times[machine], task_end_times[(job, task - 1)] if task > 0 else 0)
        end_time = start_time + duration
        ax.broken_barh([(start_time, duration)], (machine * 10, 9), facecolors=(colors[job]))
        ax.text(start_time + duration / 2, machine * 10 + 4.5, f'Project {job}, Activity {task}', ha='center', va='center', color='white')
        machine_times[machine] = end_time
        task_end_times[(job, task)] = end_time

    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Teams')
    ax.set_yticks([i * 10 + 4.5 for i in range(num_machines)])
    ax.set_yticklabels([f'Team {i}' for i in range(num_machines)])
    ax.grid(True)
    plt.show()

generate_gantt_chart(best_solution)
