import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt

class ElectricalConstructionScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("Electrical Construction Scheduler")
        self.projects = {}
        
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, padx=10, pady=10)

        add_project_button = ttk.Button(frame, text="Add Site", command=self.add_project)
        add_project_button.grid(row=0, column=0, pady=5)

        calculate_schedule_button = ttk.Button(frame, text="Calculate Schedule", command=self.calculate_schedule)
        calculate_schedule_button.grid(row=1, column=0, pady=5)

    def add_project(self):
        self.project_window = tk.Toplevel(self.root)
        self.project_window.title("Add Site and Task")

        site_label = ttk.Label(self.project_window, text="Site Name:")
        site_label.grid(row=0, column=0, padx=5, pady=5)
        self.site_entry = ttk.Entry(self.project_window)
        self.site_entry.grid(row=0, column=1, padx=5, pady=5)

        team_label = ttk.Label(self.project_window, text="Team Name:")
        team_label.grid(row=1, column=0, padx=5, pady=5)
        team_options = ["Team Engineering", "Foreman", "Electrician", "Labor", "Civil"]
        self.team_var = tk.StringVar()
        self.team_combobox = ttk.Combobox(self.project_window, textvariable=self.team_var, values=team_options, state='readonly')
        self.team_combobox.grid(row=1, column=1, padx=5, pady=5)

        activity_label = ttk.Label(self.project_window, text="Activity/Job:")
        activity_label.grid(row=2, column=0, padx=5, pady=5)
        activity_options = [
            "Checking Site", "Ordering Material (Temp Materials)", "Layouting", "Roughing Ins",
            "Hanger Support", "Wiring Support", "Devices", "Testing", "Termination", "(Civil)",
            "Load Test", "Commissioning", "Turn Over"
        ]
        self.activity_var = tk.StringVar()
        self.activity_combobox = ttk.Combobox(self.project_window, textvariable=self.activity_var, values=activity_options, state='readonly')
        self.activity_combobox.grid(row=2, column=1, padx=5, pady=5)

        duration_label = ttk.Label(self.project_window, text="Duration (Days):")
        duration_label.grid(row=3, column=0, padx=5, pady=5)
        self.duration_entry = ttk.Entry(self.project_window)
        self.duration_entry.grid(row=3, column=1, padx=5, pady=5)

        add_task_button = ttk.Button(self.project_window, text="Add Task", command=self.add_task)
        add_task_button.grid(row=4, column=0, columnspan=2, pady=5)

        save_project_button = ttk.Button(self.project_window, text="Save Site", command=self.save_project)
        save_project_button.grid(row=5, column=0, columnspan=2, pady=5)

        self.tasks = []

    def add_task(self):
        duration = self.duration_entry.get()

        if not duration.isdigit():
            messagebox.showerror("Input Error", "Please enter a valid duration.")
            return

        if not self.team_var.get() or not self.activity_var.get():
            messagebox.showerror("Input Error", "Please select a team and an activity.")
            return

        team = self.team_var.get()
        activity = self.activity_var.get()
        self.tasks.append((team, activity, int(duration)))

        self.team_combobox.set("")  # Reset the combobox selection after adding the task
        self.activity_combobox.set("")
        self.duration_entry.delete(0, tk.END)

    def save_project(self):
        site_name = self.site_entry.get()
        if not site_name:
            messagebox.showerror("Input Error", "Please enter a site name.")
            return

        if site_name in self.projects:
            messagebox.showerror("Input Error", "Site name already exists.")
            return

        self.projects[site_name] = self.tasks
        self.project_window.destroy()

    def calculate_schedule(self):
        if not self.projects:
            messagebox.showerror("Input Error", "No sites to schedule.")
            return

        jobs = []
        tasks = []
        for site, task_list in self.projects.items():
            jobs.append([(team, duration) for team, activity, duration in task_list])
            tasks.append([(team, activity) for team, activity, duration in task_list])

        best_solution, best_makespan = self.schedule_jobs(jobs, tasks)

        print("Best solution:", best_solution)
        print("Best makespan:", best_makespan)

        self.generate_gantt_chart(best_solution, jobs, tasks)

    def schedule_jobs(self, jobs, tasks):
        num_jobs = len(jobs)
        team_names = list({task[0] for job in jobs for task in job})
        team_name_to_index = {name: i for i, name in enumerate(team_names)}
        num_machines = len(team_names)
        
        pheromone_initial = 0.1
        alpha = 1.0  # Pheromone importance
        beta = 2.0   # Heuristic importance
        evaporation_rate = 0.5
        num_ants = 10
        num_iterations = 100

        pheromone = np.full((num_jobs, max(len(job) for job in jobs), num_jobs, max(len(job) for job in jobs)), pheromone_initial)

        def calculate_makespan(solution):
            machine_times = np.zeros(num_machines)
            job_end_times = np.zeros(num_jobs)
            task_end_times = {(job, task): 0 for job in range(num_jobs) for task in range(len(jobs[job]))}

            for job, task in solution:
                team, duration = jobs[job][task]
                machine = team_name_to_index[team]
                start_time = max(machine_times[machine], task_end_times[(job, task - 1)] if task > 0 else 0)
                end_time = start_time + duration
                machine_times[machine] = end_time
                task_end_times[(job, task)] = end_time
                job_end_times[job] = end_time

            return max(job_end_times)

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

        def construct_solution():
            solution = []
            remaining_tasks = [(job, task) for job in range(num_jobs) for task in range(len(jobs[job]))]
            task_end_times = {(job, task): 0 for job in range(num_jobs) for task in range(len(jobs[job]))}
            machine_times = np.zeros(num_machines)

            while remaining_tasks:
                available_tasks = [(job, task) for job, task in remaining_tasks if task == 0 or (job, task - 1) not in remaining_tasks]
                heuristic_info = [(pheromone[job][task][job][task] ** alpha) * ((1 / (machine_times[team_name_to_index[jobs[job][task][0]]] + jobs[job][task][1])) ** beta) for job, task in available_tasks]
                probabilities = np.array(heuristic_info) / np.sum(heuristic_info)
                selected_index = np.random.choice(len(available_tasks), p=probabilities)
                selected_job, selected_task = available_tasks[selected_index]
                solution.append((selected_job, selected_task))
                remaining_tasks.remove((selected_job, selected_task))
                machine_times[team_name_to_index[jobs[selected_job][selected_task][0]]] += jobs[selected_job][selected_task][1]

            return solution

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

        return best_solution, best_makespan

    def generate_gantt_chart(self, solution, jobs, tasks):
        fig, ax = plt.subplots()
        fig.patch.set_facecolor('#2e2e2e')
        ax.set_facecolor('#2e2e2e')

        # Create a mapping from team names to indices
        team_names = list({task[0] for job in jobs for task in job})
        team_name_to_index = {name: i for i, name in enumerate(team_names)}

        num_machines = len(team_names)
        machine_times = np.zeros(num_machines)
        task_end_times = {(job, task): 0 for job in range(len(jobs)) for task in range(len(jobs[job]))}
        colors = plt.cm.rainbow(np.linspace(0, 1, len(jobs)))

        for job, task in solution:
            team, duration = jobs[job][task]
            machine = team_name_to_index[team]
            start_time = max(machine_times[machine], task_end_times[(job, task - 1)] if task > 0 else 0)
            end_time = start_time + duration
            activity = tasks[job][task][1]
            ax.broken_barh([(start_time, duration)], (machine * 10, 9), facecolors=(colors[job]), edgecolor='white')
            ax.text(start_time + duration / 2, machine * 10 + 4.5, f'{activity}', ha='center', va='center', color='white')
            machine_times[machine] = end_time
            task_end_times[(job, task)] = end_time

        # Add legend
        handles = [plt.Rectangle((0, 0), 1, 1, color=colors[i]) for i in range(len(jobs))]
        labels = [site for site in self.projects.keys()]
        ax.legend(handles, labels, loc='upper left', facecolor='#2e2e2e', edgecolor='white', fontsize='small')

        ax.set_xlabel('Time (hours)', color='white')
        ax.set_ylabel('Teams', color='white')
        ax.set_yticks([i * 10 + 4.5 for i in range(num_machines)])
        ax.set_yticklabels(team_names, color='white')
        ax.grid(True, color='gray')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = ElectricalConstructionScheduler(root)
    root.mainloop()
