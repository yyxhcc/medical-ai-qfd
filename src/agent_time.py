import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('viridis')

class AgentTime:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None
        self.cleaned_df = None
        self.results = {}
        
    def load_data(self):
        print("[AgentTime] Loading data...")
        self.df = pd.read_csv(self.data_path)
        print(f"[AgentTime] Loaded {len(self.df)} records")
        return self.df
    
    def clean_data(self):
        print("[AgentTime] Cleaning waiting time data...")
        df = self.df.copy()
        
        numeric_columns = [
            'PercentageWithin4HoursAll', 
            'PercentageWithin4HoursEpisode',
            'PercentageOver8HoursEpisode',
            'PercentageOver12HoursEpisode'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        count_columns = [
            'NumberOfAttendancesAll',
            'NumberWithin4HoursAll',
            'NumberOver4HoursAll',
            'NumberOver8HoursEpisode',
            'NumberOver12HoursEpisode'
        ]
        
        for col in count_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df = df[df['AttendanceCategory'] == 'All'].copy()
        
        self.cleaned_df = df
        print(f"[AgentTime] Cleaned data shape: {self.cleaned_df.shape}")
        return self.cleaned_df
    
    def identify_bottlenecks(self):
        print("[AgentTime] Identifying bottlenecks...")
        df = self.cleaned_df
        
        results = {}
        
        if 'PercentageWithin4HoursEpisode' in df.columns:
            df['target_missed'] = df['PercentageWithin4HoursEpisode'] < 95
            low_performing = df[df['target_missed']].copy()
            
            results['low_performing_hospitals'] = low_performing.groupby('TreatmentLocation').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum',
                'NumberOver4HoursAll': 'sum'
            }).sort_values('PercentageWithin4HoursEpisode').head(10).to_dict('index')
            
            results['department_analysis'] = df.groupby('DepartmentType').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).sort_values('PercentageWithin4HoursEpisode').to_dict('index')
        
        if 'PercentageOver12HoursEpisode' in df.columns:
            results['long_wait_locations'] = df[df['PercentageOver12HoursEpisode'] > 2].groupby('TreatmentLocation').agg({
                'PercentageOver12HoursEpisode': 'mean',
                'NumberOver12HoursEpisode': 'sum'
            }).sort_values('PercentageOver12HoursEpisode', ascending=False).head(10).to_dict('index')
        
        self.results = results
        print(f"[AgentTime] Identified {len(results.get('low_performing_hospitals', {}))} bottleneck locations")
        return results
    
    def generate_figures(self, output_dir):
        print("[AgentTime] Generating figures...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df = self.cleaned_df
        
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        if 'PercentageWithin4HoursEpisode' in df.columns and 'TreatmentLocation' in df.columns:
            top_worst = df.groupby('TreatmentLocation')['PercentageWithin4HoursEpisode'].mean().nsmallest(15)
            colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(top_worst)))
            ax1.barh(range(len(top_worst)), top_worst.values, color=colors)
            ax1.set_yticks(range(len(top_worst)))
            ax1.set_yticklabels(top_worst.index)
            ax1.axvline(x=95, color='red', linestyle='--', linewidth=2, label='95% Target')
            ax1.set_xlabel('Percentage within 4 hours (%)', fontsize=11)
            ax1.set_title('Top 15 Locations with Lowest 4-Hour Compliance', fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        if 'DepartmentType' in df.columns and 'PercentageWithin4HoursEpisode' in df.columns:
            dept_perf = df.groupby('DepartmentType')['PercentageWithin4HoursEpisode'].mean().sort_values()
            colors2 = plt.cm.viridis(np.linspace(0.3, 0.9, len(dept_perf)))
            ax2.barh(range(len(dept_perf)), dept_perf.values, color=colors2)
            ax2.set_yticks(range(len(dept_perf)))
            ax2.set_yticklabels(dept_perf.index)
            ax2.axvline(x=95, color='red', linestyle='--', linewidth=2)
            ax2.set_xlabel('Percentage within 4 hours (%)', fontsize=11)
            ax2.set_title('Performance by Department Type', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        fig1.savefig(output_path / 'figure1_time_bottlenecks.pdf', dpi=300, bbox_inches='tight')
        fig1.savefig(output_path / 'figure1_time_bottlenecks.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        fig2, ax = plt.subplots(figsize=(12, 6))
        if all(col in df.columns for col in ['PercentageWithin4HoursEpisode', 'PercentageOver8HoursEpisode', 'PercentageOver12HoursEpisode']):
            wait_cats = ['Within 4h', 'Over 4h', 'Over 8h', 'Over 12h']
            wait_vals = [
                df['PercentageWithin4HoursEpisode'].mean(),
                100 - df['PercentageWithin4HoursEpisode'].mean(),
                df['PercentageOver8HoursEpisode'].mean(),
                df['PercentageOver12HoursEpisode'].mean()
            ]
            colors3 = ['#2ecc71', '#e74c3c', '#c0392b', '#922b21']
            bars = ax.bar(wait_cats, wait_vals, color=colors3, alpha=0.8, edgecolor='black', linewidth=1)
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{height:.1f}%', ha='center', va='bottom', fontsize=10)
            ax.set_ylabel('Percentage (%)', fontsize=11)
            ax.set_title('Distribution of Emergency Department Waiting Times', fontsize=13, fontweight='bold')
            ax.set_ylim(0, 105)
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            fig2.savefig(output_path / 'figure2_wait_distribution.pdf', dpi=300, bbox_inches='tight')
            fig2.savefig(output_path / 'figure2_wait_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"[AgentTime] Figures saved to {output_path}")
        
    def run(self, output_dir):
        print("="*60)
        print("AGENT TIME: 流程时序智能体 - 等候时间分析")
        print("="*60)
        
        self.load_data()
        self.clean_data()
        self.identify_bottlenecks()
        self.generate_figures(output_dir)
        
        print("[AgentTime] Analysis complete!")
        return self.results


if __name__ == "__main__":
    agent = AgentTime("../data/raw/monthly_ae_activity_202601.csv")
    results = agent.run("../output/figures")
