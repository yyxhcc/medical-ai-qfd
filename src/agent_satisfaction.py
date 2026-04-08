import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('magma')

class AgentSatisfaction:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None
        self.results = {}
        
    def load_data(self):
        print("[AgentSatisfaction] Loading data...")
        self.df = pd.read_csv(self.data_path)
        print(f"[AgentSatisfaction] Loaded {len(self.df)} records")
        return self.df
    
    def mine_demands(self):
        print("[AgentSatisfaction] Mining demands and statistics...")
        df = self.df.copy()
        
        df = df[df['AttendanceCategory'] == 'All'].copy()
        
        numeric_columns = [
            'PercentageWithin4HoursEpisode',
            'PercentageOver8HoursEpisode',
            'PercentageOver12HoursEpisode',
            'NumberOfAttendancesAll'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        results = {}
        
        if all(col in df.columns for col in ['TreatmentLocation', 'PercentageWithin4HoursEpisode', 'NumberOfAttendancesAll']):
            loc_summary = df.groupby('TreatmentLocation').agg({
                'PercentageWithin4HoursEpisode': ['mean', 'min', 'max'],
                'NumberOfAttendancesAll': 'sum'
            }).round(2)
            loc_summary.columns = ['avg_4h_rate', 'min_4h_rate', 'max_4h_rate', 'total_attendances']
            results['location_summary'] = loc_summary.sort_values('avg_4h_rate').to_dict('index')
        
        if 'DepartmentType' in df.columns:
            dept_analysis = df.groupby('DepartmentType').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'PercentageOver12HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).round(2)
            results['department_analysis'] = dept_analysis.sort_values('PercentageWithin4HoursEpisode').to_dict('index')
        
        if all(col in df.columns for col in ['PercentageWithin4HoursEpisode', 'NumberOfAttendancesAll']):
            df['demand_tier'] = pd.cut(
                df['PercentageWithin4HoursEpisode'],
                bins=[0, 85, 90, 95, 100],
                labels=['Critical', 'High Priority', 'Medium Priority', 'Good']
            )
            tier_summary = df.groupby('demand_tier').agg({
                'TreatmentLocation': 'nunique',
                'NumberOfAttendancesAll': 'sum'
            }).to_dict('index')
            results['demand_tiers'] = tier_summary
        
        if 'PercentageOver12HoursEpisode' in df.columns:
            extreme_cases = df[df['PercentageOver12HoursEpisode'] > 5].copy()
            if len(extreme_cases) > 0:
                results['extreme_wait_locations'] = extreme_cases.groupby('TreatmentLocation').agg({
                    'PercentageOver12HoursEpisode': 'mean',
                    'NumberOfAttendancesAll': 'sum'
                }).sort_values('PercentageOver12HoursEpisode', ascending=False).head(10).to_dict('index')
        
        self.results = results
        print(f"[AgentSatisfaction] Completed demand mining")
        return results
    
    def identify_shortboards(self):
        print("[AgentSatisfaction] Identifying shortboards...")
        df = self.df[self.df['AttendanceCategory'] == 'All'].copy()
        
        shortboards = {}
        
        if all(col in df.columns for col in ['PercentageWithin4HoursEpisode', 'TreatmentLocation', 'NumberOfAttendancesAll']):
            high_volume_low_perf = df[
                (df['NumberOfAttendancesAll'] > df['NumberOfAttendancesAll'].median()) &
                (df['PercentageWithin4HoursEpisode'] < 95)
            ]
            shortboards['high_volume_low_performance'] = high_volume_low_perf.groupby('TreatmentLocation').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).sort_values('PercentageWithin4HoursEpisode').head(10).to_dict('index')
        
        if 'PercentageOver8HoursEpisode' in df.columns:
            high_wait_8h = df[df['PercentageOver8HoursEpisode'] > 1].copy()
            shortboards['high_8hour_wait'] = high_wait_8h.groupby('TreatmentLocation').agg({
                'PercentageOver8HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).sort_values('PercentageOver8HoursEpisode', ascending=False).head(10).to_dict('index')
        
        self.results['shortboards'] = shortboards
        return shortboards
    
    def generate_figures(self, output_dir):
        print("[AgentSatisfaction] Generating figures...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        df = self.df[self.df['AttendanceCategory'] == 'All'].copy()
        
        fig1, ax = plt.subplots(figsize=(12, 7))
        if all(col in df.columns for col in ['PercentageWithin4HoursEpisode', 'TreatmentLocation']):
            df['demand_tier'] = pd.cut(
                df['PercentageWithin4HoursEpisode'],
                bins=[0, 85, 90, 95, 100],
                labels=['Critical (<85%)', 'High Priority (85-90%)', 'Medium Priority (90-95%)', 'Good (>95%)']
            )
            tier_counts = df['demand_tier'].value_counts().sort_index()
            colors = ['#e74c3c', '#f39c12', '#3498db', '#27ae60']
            bars = ax.bar(range(len(tier_counts)), tier_counts.values, color=colors, edgecolor='black', linewidth=1.2, alpha=0.85)
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                       f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
            ax.set_xticks(range(len(tier_counts)))
            ax.set_xticklabels(tier_counts.index, fontsize=10, rotation=15)
            ax.set_ylabel('Number of Locations', fontsize=12)
            ax.set_title('Patient Demand Tiers by 4-Hour Compliance', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            fig1.savefig(output_path / 'figure3_demand_tiers.pdf', dpi=300, bbox_inches='tight')
            fig1.savefig(output_path / 'figure3_demand_tiers.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        if 'DepartmentType' in df.columns and 'PercentageWithin4HoursEpisode' in df.columns:
            dept_stats = df.groupby('DepartmentType').agg({
                'PercentageWithin4HoursEpisode': 'mean',
                'NumberOfAttendancesAll': 'sum'
            }).sort_values('PercentageWithin4HoursEpisode')
            colors_dept = plt.cm.coolwarm(np.linspace(0, 1, len(dept_stats)))
            bars1 = ax1.barh(range(len(dept_stats)), dept_stats['PercentageWithin4HoursEpisode'], color=colors_dept, edgecolor='black', linewidth=0.8)
            ax1.set_yticks(range(len(dept_stats)))
            ax1.set_yticklabels(dept_stats.index, fontsize=10)
            ax1.axvline(x=95, color='red', linestyle='--', linewidth=2, label='95% Target')
            ax1.set_xlabel('Average 4-Hour Compliance (%)', fontsize=11)
            ax1.set_title('Performance by Department Type', fontsize=12, fontweight='bold')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            bars2 = ax2.barh(range(len(dept_stats)), dept_stats['NumberOfAttendancesAll'], color='#3498db', alpha=0.7, edgecolor='black', linewidth=0.8)
            ax2.set_yticks(range(len(dept_stats)))
            ax2.set_yticklabels(dept_stats.index, fontsize=10)
            ax2.set_xlabel('Total Attendances', fontsize=11)
            ax2.set_title('Volume by Department Type', fontsize=12, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            fig2.savefig(output_path / 'figure4_department_analysis.pdf', dpi=300, bbox_inches='tight')
            fig2.savefig(output_path / 'figure4_department_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"[AgentSatisfaction] Figures saved to {output_path}")
    
    def run(self, output_dir):
        print("="*60)
        print("AGENT SATISFACTION: 满意度分析智能体 - 诉求挖掘与分层")
        print("="*60)
        
        self.load_data()
        self.mine_demands()
        self.identify_shortboards()
        self.generate_figures(output_dir)
        
        print("[AgentSatisfaction] Analysis complete!")
        return self.results


if __name__ == "__main__":
    agent = AgentSatisfaction("../data/raw/monthly_ae_activity_202601.csv")
    results = agent.run("../output/figures")
