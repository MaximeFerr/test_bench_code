# N.Rouger // L.Leijnen
# version: Dec. 2024
# GPL3
import numpy as np
import matplotlib.pyplot as plt

# Load data
yvoltage = np.genfromtxt('csv-C4-5-Test3-valueY.csv', delimiter=',')
xtime = np.genfromtxt('csv-C4-5-Test3-timeX.csv', delimiter=',')
print(f"Loaded {len(xtime)}, {len(yvoltage)} points")
plt.plot(xtime,yvoltage)
plt.show()
