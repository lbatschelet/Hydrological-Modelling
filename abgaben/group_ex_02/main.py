#Exercise 2a – Single linear storage
# > Linear storage: the discharge is proportional to the storage content
# > Implement a simple linear storage: the flowerpot model
# > Add a constant precipitation (input) of 10mm per time step during
# the first 10 time steps.


import numpy as np
import matplotlib.pyplot as plt

# Parameters
total_time_steps = 70
precipitation_per_time_step = 10
precipitation_duration = 10
storage_content = 0
outflow_constant = 0.1
time_steps = 0

storage_content_list = []
outflow_list = []

def linear_storage(storage_content, precipitation_per_time_step, outflow_constant):
    return storage_content + precipitation_per_time_step - outflow_constant * storage_content

while time_steps < total_time_steps:
    if time_steps < precipitation_duration:
        storage_content = linear_storage(storage_content, precipitation_per_time_step, outflow_constant)
        storage_content_list.append(storage_content)
        outflow_list.append(outflow_constant * storage_content)
    else:
        storage_content = linear_storage(storage_content, 0, outflow_constant)
        storage_content_list.append(storage_content)
        outflow_list.append(outflow_constant * storage_content)
    time_steps += 1

print(storage_content_list)
print(outflow_list)

plt.plot(storage_content_list)
plt.plot(outflow_list)
plt.show()





# Exercise 2b – Storage cascade
# > Implement a storage cascade: 2 linear storages connected in series
# > The outflow from the first reservoir is the inflow to the next.
# > Each storage has its own parameter k. Get the maximum discharge
# for all 9 combinations of k1 and k2 with values = 0.1, 0.4, 0.7.




# Exercise 2c – Storage max capacity & ET
# > ET as a function of soil moisture θ and two parameters:
#   — θwp: (permanent) wilting point;
#   — θc: retention capacity, often called field capacity):




# Exercise 2c – Storage max capacity & ET
# > For a single linear reservoir, add a maximum storage capacity.
# > Then, add the ET contribution as : ET = ET0 . (S(t) / Smax)0.5
# with ET0 = 2 mm/d