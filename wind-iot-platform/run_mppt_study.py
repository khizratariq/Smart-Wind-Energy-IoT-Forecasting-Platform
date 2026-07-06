import subprocess
subprocess.run(["python", "offline_forecast.py"], check=True)
subprocess.run(["matlab", "-batch", "run('mppt_comparison.m')"], check=True)
subprocess.run(["python", "mppt_results_publisher.py"], check=True)
print("Study complete — check Grafana.")