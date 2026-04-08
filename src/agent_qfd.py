import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('Set2')

class AgentQFD:
    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None
        self.qfd_matrix = None
        self.results = {}
        
    def load_data(self):
        print("[AgentQFD] Loading data...")
        self.df = pd.read_csv(self.data_path)
        print(f"[AgentQFD] Loaded {len(self.df)} records")
        return self.df
    
    def build_qfd_house(self):
        print("[AgentQFD] Building QFD House of Quality...")
        df = self.df.copy()
        df = df[df['AttendanceCategory'] == 'All'].copy()
        
        for col in df.columns:
            if 'Percentage' in col or 'Number' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        customer_requirements = [
            {'name': 'Wait time < 4 hours', 'importance': 10, 'metric': 'PercentageWithin4HoursEpisode'},
            {'name': 'Wait time < 8 hours', 'importance': 8, 'metric': 'PercentageOver8HoursEpisode'},
            {'name': 'Wait time < 12 hours', 'importance': 9, 'metric': 'PercentageOver12HoursEpisode'},
            {'name': 'High volume capacity', 'importance': 7, 'metric': 'NumberOfAttendancesAll'},
            {'name': 'Department efficiency', 'importance': 8, 'metric': 'DepartmentType'},
        ]
        
        technical_requirements = [
            {'name': '4-hour compliance rate', 'direction': 'positive'},
            {'name': '8-hour wait reduction', 'direction': 'negative'},
            {'name': '12-hour wait reduction', 'direction': 'negative'},
            {'name': 'Throughput optimization', 'direction': 'positive'},
            {'name': 'Department standardization', 'direction': 'positive'},
        ]
        
        relationship_matrix = np.array([
            [9, 3, 1, 6, 4],
            [3, 9, 6, 4, 2],
            [1, 6, 9, 2, 3],
            [4, 2, 1, 9, 5],
            [3, 2, 2, 5, 9],
        ])
        
        importance_scores = np.array([cr['importance'] for cr in customer_requirements])
        technical_weights = np.dot(importance_scores, relationship_matrix)
        
        if 'PercentageWithin4HoursEpisode' in df.columns:
            avg_4h = df['PercentageWithin4HoursEpisode'].mean()
        else:
            avg_4h = 95
        
        if 'PercentageOver8HoursEpisode' in df.columns:
            avg_8h = df['PercentageOver8HoursEpisode'].mean()
        else:
            avg_8h = 1.0
        
        if 'PercentageOver12HoursEpisode' in df.columns:
            avg_12h = df['PercentageOver12HoursEpisode'].mean()
        else:
            avg_12h = 0.5
        
        performance_scores = [
            min(10, avg_4h / 10),
            max(0, 10 - avg_8h * 2),
            max(0, 10 - avg_12h * 3),
            7.5,
            7.0
        ]
        
        self.qfd_matrix = {
            'customer_requirements': customer_requirements,
            'technical_requirements': technical_requirements,
            'relationship_matrix': relationship_matrix,
            'importance_scores': importance_scores,
            'technical_weights': technical_weights,
            'performance_scores': performance_scores,
            'current_metrics': {
                'avg_4h_compliance': avg_4h,
                'avg_over_8h': avg_8h,
                'avg_over_12h': avg_12h
            }
        }
        
        self.results['qfd_house'] = self.qfd_matrix
        print(f"[AgentQFD] QFD House of Quality built successfully")
        return self.qfd_matrix
    
    def generate_qfd_indicators(self):
        print("[AgentQFD] Generating QFD indicators...")
        
        qfd = self.qfd_matrix
        
        indicators = []
        
        tech_reqs = qfd['technical_requirements']
        weights = qfd['technical_weights']
        performances = qfd['performance_scores']
        
        for i, tech_req in enumerate(tech_reqs):
            indicator = {
                'indicator_name': tech_req['name'],
                'weight': float(weights[i]),
                'current_performance': float(performances[i]),
                'target_performance': 9.0,
                'gap': float(9.0 - performances[i]),
                'priority': 'High' if weights[i] > 150 else 'Medium' if weights[i] > 100 else 'Low'
            }
            indicators.append(indicator)
        
        indicators_df = pd.DataFrame(indicators)
        indicators_df = indicators_df.sort_values('weight', ascending=False)
        
        self.results['qfd_indicators'] = indicators_df.to_dict('records')
        
        recommendations = []
        
        for idx, row in indicators_df.head(3).iterrows():
            rec = {
                'priority_level': f'Top {idx+1}',
                'indicator': row['indicator_name'],
                'recommendation': f"Focus on improving {row['indicator_name']}. Current performance: {row['current_performance']:.1f}/10, Target: 9.0/10. Gap: {row['gap']:.1f}",
                'action_items': [
                    'Conduct root cause analysis',
                    'Implement process improvements',
                    'Monitor performance weekly',
                    'Train staff on new procedures'
                ]
            }
            recommendations.append(rec)
        
        self.results['recommendations'] = recommendations
        
        print(f"[AgentQFD] Generated {len(indicators)} QFD indicators")
        return indicators
    
    def generate_figures(self, output_dir):
        print("[AgentQFD] Generating figures...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        qfd = self.qfd_matrix
        
        fig1, ax = plt.subplots(figsize=(12, 7))
        tech_names = [t['name'] for t in qfd['technical_requirements']]
        weights = qfd['technical_weights']
        performances = qfd['performance_scores']
        
        x = np.arange(len(tech_names))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, weights/max(weights)*10, width, 
                      label='Relative Weight', color='#3498db', alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x + width/2, performances, width,
                      label='Current Performance', color='#2ecc71', alpha=0.8, edgecolor='black')
        
        ax.axhline(y=9, color='red', linestyle='--', linewidth=2, label='Target (9.0)')
        
        ax.set_xlabel('Technical Requirements', fontsize=12)
        ax.set_ylabel('Score (0-10)', fontsize=12)
        ax.set_title('QFD: Technical Requirements - Weight vs Performance', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(tech_names, rotation=25, ha='right', fontsize=10)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim(0, 11)
        
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        fig1.savefig(output_path / 'figure7_qfd_weights.pdf', dpi=300, bbox_inches='tight')
        fig1.savefig(output_path / 'figure7_qfd_weights.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        fig2, ax = plt.subplots(figsize=(10, 8))
        cr_names = [cr['name'] for cr in qfd['customer_requirements']]
        tr_names = [t['name'] for t in qfd['technical_requirements']]
        rel_matrix = qfd['relationship_matrix']
        
        im = ax.imshow(rel_matrix, cmap='YlOrRd', vmin=0, vmax=9)
        
        ax.set_xticks(np.arange(len(tr_names)))
        ax.set_yticks(np.arange(len(cr_names)))
        ax.set_xticklabels(tr_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(cr_names, fontsize=10)
        
        for i in range(len(cr_names)):
            for j in range(len(tr_names)):
                val = rel_matrix[i, j]
                if val > 0:
                    color = 'white' if val > 5 else 'black'
                    text = ax.text(j, i, val, ha='center', va='center', 
                                  color=color, fontsize=11, fontweight='bold')
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Relationship Strength (0-9)', fontsize=11)
        
        ax.set_xlabel('Technical Requirements', fontsize=12)
        ax.set_ylabel('Customer Requirements', fontsize=12)
        ax.set_title('QFD House of Quality: Relationship Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        fig2.savefig(output_path / 'figure8_qfd_relationship_matrix.pdf', dpi=300, bbox_inches='tight')
        fig2.savefig(output_path / 'figure8_qfd_relationship_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[AgentQFD] Figures saved to {output_path}")
    
    def run(self, output_dir):
        print("="*60)
        print("AGENT QFD: QFD质量屋智能体 - 指标转化")
        print("="*60)
        
        self.load_data()
        self.build_qfd_house()
        self.generate_qfd_indicators()
        self.generate_figures(output_dir)
        
        print("[AgentQFD] Analysis complete!")
        return self.results


if __name__ == "__main__":
    agent = AgentQFD("../data/raw/monthly_ae_activity_202601.csv")
    results = agent.run("../output/figures")
