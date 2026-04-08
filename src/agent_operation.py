import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('rocket')

class AgentOperation:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None
        self.cleaned_df = None
        self.results = {}
        
    def load_data(self):
        print("[AgentOperation] Loading data...")
        self.df = pd.read_csv(self.data_path)
        print(f"[AgentOperation] Loaded {len(self.df)} records")
        return self.df
    
    def integrate_data(self):
        print("[AgentOperation] Integrating business data...")
        df = self.df.copy()
        
        df = df[df['AttendanceCategory'] == 'All'].copy()
        
        numeric_columns = [
            'NumberOfAttendancesAll',
            'NumberWithin4HoursAll',
            'NumberOver4HoursAll',
            'PercentageWithin4HoursAll',
            'PercentageWithin4HoursEpisode',
            'PercentageOver8HoursEpisode',
            'PercentageOver12HoursEpisode',
            'NumberOver8HoursEpisode',
            'NumberOver12HoursEpisode'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        self.cleaned_df = df
        print(f"[AgentOperation] Integrated data shape: {self.cleaned_df.shape}")
        return self.cleaned_df
    
    def identify_process_breakpoints(self):
        print("[AgentOperation] Identifying process breakpoints...")
        df = self.cleaned_df
        
        results = {}
        
        if all(col in df.columns for col in ['TreatmentLocation', 'PercentageWithin4HoursEpisode', 'NumberOfAttendancesAll']):
            loc_breakpoints = df.groupby('TreatmentLocation').agg({
                'PercentageWithin4HoursEpisode': ['mean', 'std'],
                'NumberOfAttendancesAll': 'sum',
                'NumberOver4HoursAll': 'sum',
                'PercentageOver8HoursEpisode': 'mean',
                'PercentageOver12HoursEpisode': 'mean'
            }).round(3)
            
            loc_breakpoints.columns = ['avg_4h_compliance', 'std_4h_compliance', 
                                       'total_attendances', 'total_over_4h',
                                       'avg_over_8h', 'avg_over_12h']
            
            loc_breakpoints['efficiency_score'] = (
                loc_breakpoints['avg_4h_compliance'] * 0.6 +
                (100 - loc_breakpoints['avg_over_8h']) * 0.25 +
                (100 - loc_breakpoints['avg_over_12h']) * 0.15
            )
            
            results['location_breakpoints'] = loc_breakpoints.sort_values('efficiency_score').to_dict('index')
            results['low_efficiency_locations'] = loc_breakpoints[loc_breakpoints['efficiency_score'] < 90].sort_values('efficiency_score').head(15).to_dict('index')
        
        if 'DepartmentType' in df.columns:
            dept_breakpoints = df.groupby('DepartmentType').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'PercentageOver8HoursEpisode': 'mean',
                'PercentageOver12HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).round(2)
            
            dept_breakpoints['process_breakpoint_flag'] = (
                (dept_breakpoints['PercentageWithin4HoursEpisode'] < 95) |
                (dept_breakpoints['PercentageOver8HoursEpisode'] > 1)
            )
            
            results['department_breakpoints'] = dept_breakpoints.sort_values('PercentageWithin4HoursEpisode').to_dict('index')
        
        if 'HBT' in df.columns:
            hbt_analysis = df.groupby('HBT').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum',
                'TreatmentLocation': 'nunique'
            }).round(2)
            hbt_analysis.columns = ['avg_4h_compliance', 'total_attendances', 'num_locations']
            results['hbt_regional_analysis'] = hbt_analysis.sort_values('avg_4h_compliance').to_dict('index')
        
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], format='%Y%m', errors='coerce')
            if df['Month'].notna().any():
                monthly_trend = df.groupby('Month').agg({
                    'PercentageWithin4HoursEpisode': 'mean',
                    'NumberOfAttendancesAll': 'sum'
                }).round(2)
                results['monthly_trend'] = monthly_trend.to_dict('index')
        
        self.results = results
        print(f"[AgentOperation] Identified process breakpoints")
        return results
    
    def generate_figures(self, output_dir):
        print("[AgentOperation] Generating figures...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df = self.cleaned_df
        
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        if all(col in df.columns for col in ['TreatmentLocation', 'PercentageWithin4HoursEpisode', 'NumberOfAttendancesAll']):
            loc_summary = df.groupby('TreatmentLocation').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).sort_values('PercentageWithin4HoursEpisode')
            
            bottom_15 = loc_summary.head(15)
            colors = plt.cm.RdYlGn_r(np.linspace(0, 1, len(bottom_15)))
            bars1 = ax1.barh(range(len(bottom_15)), bottom_15['PercentageWithin4HoursEpisode'], color=colors, edgecolor='black', linewidth=0.8)
            ax1.set_yticks(range(len(bottom_15)))
            ax1.set_yticklabels(bottom_15.index, fontsize=9)
            ax1.axvline(x=95, color='red', linestyle='--', linewidth=2, label='95% Target')
            ax1.set_xlabel('4-Hour Compliance (%)', fontsize=11)
            ax1.set_title('Bottom 15 Locations by Efficiency', fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            top_10 = loc_summary.tail(10)
            colors2 = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(top_10)))
            bars2 = ax2.barh(range(len(top_10)), top_10['PercentageWithin4HoursEpisode'], color=colors2, edgecolor='black', linewidth=0.8)
            ax2.set_yticks(range(len(top_10)))
            ax2.set_yticklabels(top_10.index, fontsize=9)
            ax2.axvline(x=95, color='green', linestyle='--', linewidth=2)
            ax2.set_xlabel('4-Hour Compliance (%)', fontsize=11)
            ax2.set_title('Top 10 Locations by Efficiency', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            fig1.savefig(output_path / 'figure5_operation_efficiency.pdf', dpi=300, bbox_inches='tight')
            fig1.savefig(output_path / 'figure5_operation_efficiency.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        fig2, ax = plt.subplots(figsize=(12, 7))
        if 'HBT' in df.columns and 'PercentageWithin4HoursEpisode' in df.columns:
            hbt_stats = df.groupby('HBT')['PercentageWithin4HoursEpisode'].agg(['mean', 'count']).sort_values('mean')
            colors_hbt = plt.cm.viridis(np.linspace(0.2, 0.9, len(hbt_stats)))
            bars = ax.barh(range(len(hbt_stats)), hbt_stats['mean'], color=colors_hbt, edgecolor='black', linewidth=0.8)
            for i, (idx, row) in enumerate(hbt_stats.iterrows()):
                ax.text(row['mean'] + 0.5, i, f"n={int(row['count'])}", va='center', fontsize=9)
            ax.set_yticks(range(len(hbt_stats)))
            ax.set_yticklabels(hbt_stats.index, fontsize=10)
            ax.axvline(x=95, color='red', linestyle='--', linewidth=2)
            ax.set_xlabel('Average 4-Hour Compliance (%)', fontsize=12)
            ax.set_title('Regional Performance by Health Board', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            fig2.savefig(output_path / 'figure6_regional_comparison.pdf', dpi=300, bbox_inches='tight')
            fig2.savefig(output_path / 'figure6_regional_comparison.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"[AgentOperation] Figures saved to {output_path}")
    
    def run(self, output_dir):
        print("="*60)
        print("AGENT OPERATION: 业务运营智能体 - 流程断点识别")
        print("="*60)
        
        self.load_data()
        self.integrate_data()
        self.identify_process_breakpoints()
        self.generate_figures(output_dir)
        
        print("[AgentOperation] Analysis complete!")
        return self.results


if __name__ == "__main__":
    agent = AgentOperation("../data/raw/monthly_ae_activity_202601.csv")
    results = agent.run("../output/figures")
