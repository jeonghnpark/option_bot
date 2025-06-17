import time

current_time = time.time()

print(current_time)
time.sleep(1)
current_time2 = time.time()
print(current_time2)
print(f"elapsed time {current_time2 - current_time}")
