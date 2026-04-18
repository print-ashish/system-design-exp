import matplotlib.pyplot as plt
import numpy as np
import json
import os

def create_linkedin_visual(data_lock, data_no_lock, output_file="concurrency_results.png"):
    # Modern dark theme styling
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    fig.patch.set_facecolor('#0d1117')
    
    # --- Chart 1: Booking Integrity (Goal: Exactly 1) ---
    metrics = ['Seats Sold']
    lock_vals = [data_lock['success']]
    no_lock_vals = [data_no_lock['success']]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    ax1.bar(x - width/2, lock_vals, width, label='With Distributed Lock', color='#3fb950', edgecolor='white', alpha=0.9)
    ax1.bar(x + width/2, no_lock_vals, width, label='Without Lock (Broke!)', color='#f85149', edgecolor='white', alpha=0.9)
    
    ax1.set_ylabel('Success Count')
    ax1.set_title('Data Integrity: Who got the seat?', fontsize=16, pad=20, color='#58a6ff')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics)
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Add target line
    ax1.axhline(y=1, color='white', linestyle='--', alpha=0.5, label='Actual Availability')

    # --- Chart 2: Request Distribution ---
    labels = ['Success', 'Redis Block', 'Cache Hit', 'DB Block']
    
    # Lock Stats
    lock_dist = [
        data_lock['success'], 
        data_lock['lock_blocked'], 
        data_lock['cache_hits'], 
        data_lock['db_blocked']
    ]
    
    # No Lock Stats
    no_lock_dist = [
        data_no_lock['success'], 
        0, # No Redis blocks
        data_no_lock['cache_hits'], 
        data_no_lock['db_blocked']
    ]

    x2 = np.arange(len(labels))
    ax2.bar(x2 - width/2, lock_dist, width, label='With Lock', color='#58a6ff', alpha=0.8)
    ax2.bar(x2 + width/2, no_lock_dist, width, label='Without Lock', color='#bc8cff', alpha=0.8)
    
    ax2.set_ylabel('Request Count')
    ax2.set_title('How were 1000 requests handled?', fontsize=16, pad=20, color='#bc8cff')
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels)
    ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.3)

    plt.suptitle('High-Concurrency Seat Booking System: System Design Experiment', fontsize=22, y=1.05, color='white', fontweight='bold')
    plt.tight_layout()
    
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='#0d1117')
    print(f"\n[✓] LinkedIn infographic saved to: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    # Sample data for standalone testing
    sample_lock = {"success": 1, "lock_blocked": 95, "cache_hits": 904, "db_blocked": 0}
    sample_no_lock = {"success": 3, "lock_blocked": 0, "cache_hits": 912, "db_blocked": 85}
    create_linkedin_visual(sample_lock, sample_no_lock)
