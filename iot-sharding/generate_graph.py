import matplotlib.pyplot as plt
import numpy as np

# YOUR ACTUAL DATA
categories = ['Throughput Time\n(100k writes)', 'System Availability\n(during node failure)']

# Left bar: Monolith | Right bar: Sharding
monolith_data = [93, 0]    # 93 seconds, 0% availability
sharding_data = [106, 66.7] # 106 seconds, 66.7% availability

x = np.arange(len(categories))
width = 0.35

fig, ax1 = plt.subplots(figsize=(10, 6))

# Plotting the bars
rects1 = ax1.bar(x - width/2, monolith_data, width, label='Monolith (Single DB)', color='#ff9999') # Soft Red
rects2 = ax1.bar(x + width/2, sharding_data, width, label='Sharded System (3 Nodes)', color='#66b3ff') # Soft Blue

# Add labels and formatting
ax1.set_ylabel('Measured Values', fontweight='bold')
ax1.set_title('Monolith vs. Sharding: The "Reliability Tax" Trade-off', fontsize=14, pad=20, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontweight='bold')
ax1.legend()

# Add value labels on top of the bars
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        label = f'{height}s' if height > 80 else f'{height}%'
        if height == 0: label = "CRASHED"
        ax1.annotate(label,
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')

autolabel(rects1)
autolabel(rects2)

plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

plt.savefig('actual_sharding_results.png', dpi=300)
print("✅ Honest Graph generated: actual_sharding_results.png")
plt.show()
