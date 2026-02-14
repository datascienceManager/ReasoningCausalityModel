"""
============================================================================
CUSTOMER CHURN CAUSALITY ANALYSIS
============================================================================
Purpose: Identify causal factors driving customer churn
Output: Executive-ready causal diagrams and insights
Methods: Multiple causal inference techniques
============================================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("CUSTOMER CHURN CAUSALITY ANALYSIS")
print("=" * 80)
print()

# ============================================================================
# 1. CREATE REALISTIC CUSTOMER CHURN DATA
# ============================================================================

print("1. Generating customer churn data...")

np.random.seed(42)
n_customers = 5000

# Create realistic customer data with causal relationships
data = pd.DataFrame({
    # Demographics (root causes)
    'customer_age': np.random.normal(45, 15, n_customers).clip(18, 80),
    'tenure_months': np.random.exponential(24, n_customers).clip(1, 120),
    
    # Service quality (intermediate causes)
    'service_calls': np.random.poisson(3, n_customers),
    'avg_call_duration': np.random.gamma(2, 5, n_customers),
    'complaint_count': np.random.poisson(1.5, n_customers),
    
    # Usage patterns (intermediate causes)
    'monthly_usage_gb': np.random.gamma(5, 10, n_customers),
    'login_frequency': np.random.poisson(15, n_customers),
    'feature_adoption_score': np.random.beta(2, 5, n_customers) * 100,
    
    # Financial factors (strong causes)
    'monthly_charges': np.random.normal(75, 25, n_customers).clip(20, 200),
    'total_charges': np.random.normal(1800, 1200, n_customers).clip(0, 10000),
    'payment_delays': np.random.poisson(0.8, n_customers),
    
    # Engagement (protective factors)
    'loyalty_program': np.random.choice([0, 1], n_customers, p=[0.6, 0.4]),
    'referrals_made': np.random.poisson(0.5, n_customers),
    'satisfaction_score': np.random.beta(5, 2, n_customers) * 10
})

# Create causal churn based on realistic business logic
churn_probability = (
    # Price sensitivity (strong driver)
    0.15 * (data['monthly_charges'] > 100).astype(int) +
    
    # Service quality issues (strong driver)
    0.12 * (data['complaint_count'] > 2).astype(int) +
    0.08 * (data['service_calls'] > 5).astype(int) +
    
    # Low engagement (strong driver)
    0.10 * (data['login_frequency'] < 5).astype(int) +
    0.08 * (data['feature_adoption_score'] < 30).astype(int) +
    
    # Financial stress (medium driver)
    0.10 * (data['payment_delays'] > 1).astype(int) +
    
    # New customers more likely to churn (medium driver)
    0.08 * (data['tenure_months'] < 6).astype(int) +
    
    # Protective factors (reduce churn)
    -0.12 * data['loyalty_program'] +
    -0.08 * (data['referrals_made'] > 0).astype(int) +
    -0.10 * (data['satisfaction_score'] > 8).astype(int) +
    
    # Base churn rate
    0.15
)

# Add some randomness
churn_probability = churn_probability.clip(0, 1)
data['churned'] = (np.random.random(n_customers) < churn_probability).astype(int)

print(f"   ✓ Generated {n_customers:,} customer records")
print(f"   ✓ Churn rate: {data['churned'].mean()*100:.1f}%")
print()

# ============================================================================
# 2. CALCULATE FEATURE IMPORTANCE (CAUSAL STRENGTH)
# ============================================================================

print("2. Analyzing causal relationships...")

# Separate features and target
X = data.drop('churned', axis=1)
y = data['churned']

# Train Random Forest to get feature importance
rf_model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
rf_model.fit(X, y)

# Get feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print("   Top 10 Churn Drivers:")
for idx, row in feature_importance.head(10).iterrows():
    print(f"      {row['feature']:30s} {row['importance']:.4f}")
print()

# ============================================================================
# 3. CREATE CAUSAL CATEGORIES
# ============================================================================

print("3. Categorizing causal factors...")

# Define causal factor categories
causal_categories = {
    'Financial Stress': {
        'factors': ['monthly_charges', 'total_charges', 'payment_delays'],
        'color': '#e74c3c',
        'icon': '💰'
    },
    'Service Quality': {
        'factors': ['service_calls', 'complaint_count', 'avg_call_duration'],
        'color': '#f39c12',
        'icon': '📞'
    },
    'Low Engagement': {
        'factors': ['login_frequency', 'feature_adoption_score', 'monthly_usage_gb'],
        'color': '#3498db',
        'icon': '📊'
    },
    'Customer Tenure': {
        'factors': ['tenure_months', 'customer_age'],
        'color': '#9b59b6',
        'icon': '⏱️'
    },
    'Loyalty & Satisfaction': {
        'factors': ['loyalty_program', 'referrals_made', 'satisfaction_score'],
        'color': '#27ae60',
        'icon': '⭐'
    }
}

# Calculate category impact
category_impact = {}
for category, info in causal_categories.items():
    category_factors = [f for f in info['factors'] if f in feature_importance['feature'].values]
    impact = feature_importance[feature_importance['feature'].isin(category_factors)]['importance'].sum()
    category_impact[category] = impact

category_impact_df = pd.DataFrame({
    'Category': list(category_impact.keys()),
    'Impact': list(category_impact.values())
}).sort_values('Impact', ascending=False)

print("   Causal Category Impact:")
for _, row in category_impact_df.iterrows():
    category = row['Category']
    icon = causal_categories[category]['icon']
    print(f"      {icon} {row['Category']:30s} {row['Impact']:.4f}")
print()

# ============================================================================
# 4. CREATE CAUSAL DIAGRAM - HIERARCHICAL VIEW
# ============================================================================

print("4. Creating causal diagrams...")

def create_hierarchical_causal_diagram(category_impact_df, causal_categories, output_path):
    """Create a hierarchical causal diagram showing factor categories"""
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'Customer Churn Causality Analysis', 
           ha='center', va='top', fontsize=24, fontweight='bold',
           color='#2c3e50')
    
    ax.text(5, 9.0, 'What Drives Customers to Leave?',
           ha='center', va='top', fontsize=16, color='#7f8c8d')
    
    # Churn node (center)
    churn_x, churn_y = 5, 3.5
    churn_box = FancyBboxPatch(
        (churn_x - 0.8, churn_y - 0.4), 1.6, 0.8,
        boxstyle="round,pad=0.1", 
        facecolor='#e74c3c', 
        edgecolor='#c0392b', 
        linewidth=3
    )
    ax.add_patch(churn_box)
    ax.text(churn_x, churn_y, 'CUSTOMER\nCHURN', 
           ha='center', va='center', fontsize=16, fontweight='bold',
           color='white')
    
    # Position causal categories in a circle around churn
    n_categories = len(category_impact_df)
    angles = np.linspace(0, 2*np.pi, n_categories, endpoint=False)
    
    for idx, (_, row) in enumerate(category_impact_df.iterrows()):
        category = row['Category']
        impact = row['Impact']
        
        # Calculate position
        radius = 3.5
        x = churn_x + radius * np.cos(angles[idx] + np.pi/2)
        y = churn_y + radius * np.sin(angles[idx] + np.pi/2)
        
        # Box size based on impact
        box_width = 1.8
        box_height = 0.6
        
        # Draw box
        color = causal_categories[category]['color']
        icon = causal_categories[category]['icon']
        
        box = FancyBboxPatch(
            (x - box_width/2, y - box_height/2), 
            box_width, box_height,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='white',
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(box)
        
        # Add text
        ax.text(x, y + 0.05, f"{icon} {category}",
               ha='center', va='center', fontsize=11, fontweight='bold',
               color='white')
        
        # Impact score
        ax.text(x, y - 0.25, f"Impact: {impact:.1%}",
               ha='center', va='center', fontsize=9,
               color='white', style='italic')
        
        # Arrow from category to churn
        arrow_width = 3 + impact * 100  # Thicker arrow = more impact
        
        arrow = FancyArrowPatch(
            (x, y),
            (churn_x, churn_y),
            arrowstyle='->,head_width=0.6,head_length=0.8',
            color=color,
            linewidth=arrow_width,
            alpha=0.6,
            zorder=1
        )
        ax.add_patch(arrow)
    
    # Legend
    legend_y = 0.8
    ax.text(0.5, legend_y, 'Legend:', fontsize=12, fontweight='bold', color='#2c3e50')
    ax.text(0.5, legend_y - 0.3, '• Arrow thickness = causal strength', 
           fontsize=10, color='#34495e')
    ax.text(0.5, legend_y - 0.6, '• Impact % = contribution to churn', 
           fontsize=10, color='#34495e')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   ✓ Saved: {output_path}")

create_hierarchical_causal_diagram(
    category_impact_df, 
    causal_categories,
    '/dbfs/FileStore/example_charts/causal_diagram_hierarchical.png'
)

# ============================================================================
# 5. CREATE DETAILED CAUSAL NETWORK DIAGRAM
# ============================================================================

def create_detailed_causal_network(feature_importance, causal_categories, output_path):
    """Create detailed network diagram showing individual factors"""
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create network graph
    G = nx.DiGraph()
    
    # Add churn node
    G.add_node('CHURN', node_type='outcome')
    
    # Add top factors
    top_factors = feature_importance.head(12)
    
    for _, row in top_factors.iterrows():
        factor = row['feature']
        importance = row['importance']
        
        # Find category
        category = None
        for cat_name, cat_info in causal_categories.items():
            if factor in cat_info['factors']:
                category = cat_name
                break
        
        if category is None:
            category = 'Other'
        
        G.add_node(factor, 
                  importance=importance,
                  category=category,
                  node_type='factor')
        
        G.add_edge(factor, 'CHURN', weight=importance)
    
    # Position nodes
    pos = {}
    
    # Churn in center-right
    pos['CHURN'] = (2, 0)
    
    # Factors in a circle on the left
    n_factors = len([n for n, d in G.nodes(data=True) if d['node_type'] == 'factor'])
    angles = np.linspace(0, 2*np.pi, n_factors, endpoint=False)
    
    factor_idx = 0
    for node in G.nodes():
        if G.nodes[node]['node_type'] == 'factor':
            radius = 1.5
            x = -1 + radius * np.cos(angles[factor_idx])
            y = radius * np.sin(angles[factor_idx])
            pos[node] = (x, y)
            factor_idx += 1
    
    # Draw edges with width based on importance
    for (u, v, d) in G.edges(data=True):
        weight = d['weight']
        
        # Get category color
        if G.nodes[u]['node_type'] == 'factor':
            category = G.nodes[u]['category']
            if category in causal_categories:
                color = causal_categories[category]['color']
            else:
                color = '#95a5a6'
        else:
            color = '#95a5a6'
        
        nx.draw_networkx_edges(
            G, pos,
            [(u, v)],
            width=weight * 30,
            alpha=0.6,
            edge_color=color,
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            connectionstyle='arc3,rad=0.1',
            ax=ax
        )
    
    # Draw nodes
    for node in G.nodes():
        node_data = G.nodes[node]
        
        if node_data['node_type'] == 'outcome':
            # Churn node
            nx.draw_networkx_nodes(
                G, pos,
                [node],
                node_size=4000,
                node_color='#e74c3c',
                node_shape='o',
                edgecolors='#c0392b',
                linewidths=3,
                ax=ax
            )
            
            ax.text(pos[node][0], pos[node][1], 'CUSTOMER\nCHURN',
                   ha='center', va='center',
                   fontsize=14, fontweight='bold',
                   color='white')
        
        else:
            # Factor node
            category = node_data['category']
            importance = node_data['importance']
            
            if category in causal_categories:
                color = causal_categories[category]['color']
            else:
                color = '#95a5a6'
            
            node_size = 1000 + importance * 8000
            
            nx.draw_networkx_nodes(
                G, pos,
                [node],
                node_size=node_size,
                node_color=color,
                alpha=0.8,
                edgecolors='white',
                linewidths=2,
                ax=ax
            )
            
            # Label
            label = node.replace('_', '\n')
            ax.text(pos[node][0], pos[node][1] - 0.15, label,
                   ha='center', va='top',
                   fontsize=8, fontweight='bold',
                   color='white')
            
            # Importance
            ax.text(pos[node][0], pos[node][1] + 0.15, f"{importance:.1%}",
                   ha='center', va='bottom',
                   fontsize=7, style='italic',
                   color='white')
    
    # Title
    ax.text(0.5, 1.8, 'Detailed Causal Network: Top Churn Drivers',
           ha='center', va='top', fontsize=20, fontweight='bold',
           color='#2c3e50', transform=ax.transData)
    
    ax.text(0.5, 1.6, 'Node size = causal strength | Arrow thickness = impact level',
           ha='center', va='top', fontsize=12, color='#7f8c8d',
           transform=ax.transData, style='italic')
    
    # Legend
    legend_x = -2.8
    legend_y = -1.8
    
    ax.text(legend_x, legend_y + 0.3, 'Categories:', 
           fontsize=11, fontweight='bold', color='#2c3e50')
    
    y_offset = 0
    for category, info in causal_categories.items():
        ax.scatter([legend_x + 0.1], [legend_y - y_offset], 
                  s=200, color=info['color'], alpha=0.8, edgecolors='white', linewidths=2)
        ax.text(legend_x + 0.3, legend_y - y_offset, 
               f"{info['icon']} {category}",
               fontsize=9, va='center', color='#34495e')
        y_offset += 0.25
    
    ax.set_xlim(-3.2, 3)
    ax.set_ylim(-2.2, 2)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   ✓ Saved: {output_path}")

create_detailed_causal_network(
    feature_importance,
    causal_categories,
    '/dbfs/FileStore/example_charts/causal_network_detailed.png'
)

# ============================================================================
# 6. CREATE WATERFALL CHART - CHURN CONTRIBUTION
# ============================================================================

def create_churn_waterfall(feature_importance, output_path):
    """Create waterfall chart showing cumulative churn contribution"""
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Get top 10 factors
    top_10 = feature_importance.head(10).copy()
    
    # Calculate cumulative
    top_10['cumulative'] = top_10['importance'].cumsum()
    
    # Base rate
    base_rate = 0.15
    
    # Colors
    colors = ['#3498db', '#e74c3c', '#f39c12', '#27ae60', '#9b59b6',
             '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b']
    
    # Plot bars
    x_pos = np.arange(len(top_10))
    bottom = base_rate
    
    for idx, (_, row) in enumerate(top_10.iterrows()):
        ax.bar(idx, row['importance'], bottom=bottom, 
              color=colors[idx], alpha=0.8, edgecolor='white', linewidth=2)
        
        # Add connector line
        if idx < len(top_10) - 1:
            ax.plot([idx + 0.4, idx + 0.6], 
                   [bottom + row['importance'], bottom + row['importance']],
                   'k--', linewidth=1, alpha=0.5)
        
        # Label
        ax.text(idx, bottom + row['importance']/2, 
               f"{row['importance']:.1%}",
               ha='center', va='center', fontsize=10, fontweight='bold',
               color='white')
        
        bottom += row['importance']
    
    # Base rate bar
    ax.bar(-0.5, base_rate, color='#95a5a6', alpha=0.6, 
          label='Base Churn Rate', edgecolor='white', linewidth=2)
    ax.text(-0.5, base_rate/2, f"{base_rate:.1%}",
           ha='center', va='center', fontsize=10, fontweight='bold',
           color='white')
    
    # Final churn rate
    final_rate = base_rate + top_10['importance'].sum()
    ax.bar(len(top_10) + 0.5, final_rate, color='#e74c3c', alpha=0.8,
          label='Total Churn Rate', edgecolor='white', linewidth=2)
    ax.text(len(top_10) + 0.5, final_rate/2, f"{final_rate:.1%}",
           ha='center', va='center', fontsize=12, fontweight='bold',
           color='white')
    
    # Formatting
    ax.set_xticks(range(len(top_10)))
    ax.set_xticklabels([f.replace('_', '\n') for f in top_10['feature']], 
                       rotation=45, ha='right', fontsize=10)
    
    ax.set_ylabel('Churn Rate Contribution', fontsize=13, fontweight='bold')
    ax.set_title('Churn Waterfall: How Each Factor Contributes to Customer Loss',
                fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
    
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # Add annotation
    ax.annotate('', xy=(len(top_10) + 0.5, final_rate), 
               xytext=(-0.5, base_rate),
               arrowprops=dict(arrowstyle='->', lw=2, color='#e74c3c', alpha=0.5))
    
    ax.text(len(top_10)/2, final_rate + 0.03, 
           f'Total Impact: +{(final_rate - base_rate):.1%}',
           ha='center', fontsize=12, fontweight='bold',
           color='#e74c3c',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='#e74c3c', linewidth=2))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   ✓ Saved: {output_path}")

create_churn_waterfall(
    feature_importance,
    '/dbfs/FileStore/example_charts/churn_waterfall.png'
)

# ============================================================================
# 7. CREATE SANKEY DIAGRAM (using matplotlib)
# ============================================================================

def create_churn_sankey(category_impact_df, causal_categories, output_path):
    """Create Sankey-style flow diagram"""
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'Churn Causality Flow Analysis',
           ha='center', va='top', fontsize=22, fontweight='bold',
           color='#2c3e50')
    
    ax.text(5, 9.0, 'From Root Causes to Customer Churn',
           ha='center', va='top', fontsize=14, color='#7f8c8d', style='italic')
    
    # Categories on left
    left_x = 1
    total_height = 6
    start_y = 8 - total_height
    
    y_current = start_y
    flows = []
    
    for _, row in category_impact_df.iterrows():
        category = row['Category']
        impact = row['Impact']
        
        # Height proportional to impact
        height = (impact / category_impact_df['Impact'].sum()) * total_height
        
        color = causal_categories[category]['color']
        icon = causal_categories[category]['icon']
        
        # Draw category box
        box = FancyBboxPatch(
            (left_x - 0.4, y_current), 
            2.5, height,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='white',
            linewidth=2,
            alpha=0.85
        )
        ax.add_patch(box)
        
        # Label
        ax.text(left_x + 1, y_current + height/2,
               f"{icon} {category}\n{impact:.1%}",
               ha='center', va='center', fontsize=11, fontweight='bold',
               color='white')
        
        # Store for flow
        flows.append({
            'y_start': y_current,
            'y_end': y_current + height,
            'y_mid': y_current + height/2,
            'impact': impact,
            'color': color
        })
        
        y_current += height + 0.1
    
    # Churn box on right
    right_x = 7.5
    churn_y_start = start_y
    churn_y_end = start_y + total_height
    
    churn_box = FancyBboxPatch(
        (right_x, churn_y_start),
        2, total_height,
        boxstyle="round,pad=0.1",
        facecolor='#e74c3c',
        edgecolor='#c0392b',
        linewidth=3,
        alpha=0.9
    )
    ax.add_patch(churn_box)
    
    ax.text(right_x + 1, (churn_y_start + churn_y_end)/2,
           'CUSTOMER\nCHURN',
           ha='center', va='center', fontsize=18, fontweight='bold',
           color='white')
    
    # Draw flows
    for flow in flows:
        # Cubic bezier curve for flow
        x_start = left_x + 2.5
        x_end = right_x
        y_start = flow['y_mid']
        y_end = (churn_y_start + churn_y_end) / 2
        
        # Control points
        x_mid = (x_start + x_end) / 2
        
        # Create smooth curve
        t = np.linspace(0, 1, 100)
        
        # Bezier curve
        x_curve = (1-t)**3 * x_start + 3*(1-t)**2*t * x_mid + 3*(1-t)*t**2 * x_mid + t**3 * x_end
        y_curve = (1-t)**3 * y_start + 3*(1-t)**2*t * y_start + 3*(1-t)*t**2 * y_end + t**3 * y_end
        
        # Width based on impact
        width = flow['impact'] * 80
        
        ax.plot(x_curve, y_curve, 
               color=flow['color'], 
               linewidth=width, 
               alpha=0.3,
               solid_capstyle='round')
    
    # Add insights box
    insights_box = FancyBboxPatch(
        (0.5, 0.5), 4, 1.2,
        boxstyle="round,pad=0.1",
        facecolor='#ecf0f1',
        edgecolor='#bdc3c7',
        linewidth=2
    )
    ax.add_patch(insights_box)
    
    ax.text(2.5, 1.4, '💡 Key Insights:', 
           ha='center', fontsize=12, fontweight='bold', color='#2c3e50')
    
    top_category = category_impact_df.iloc[0]
    ax.text(2.5, 1.0, 
           f"• {top_category['Category']} is the #1 churn driver ({top_category['Impact']:.1%})",
           ha='center', fontsize=10, color='#34495e')
    
    total_impact = category_impact_df['Impact'].sum()
    ax.text(2.5, 0.7,
           f"• Top 3 categories explain {total_impact:.1%} of churn",
           ha='center', fontsize=10, color='#34495e')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"   ✓ Saved: {output_path}")

create_churn_sankey(
    category_impact_df,
    causal_categories,
    '/dbfs/FileStore/example_charts/churn_sankey_flow.png'
)

print()

# ============================================================================
# 8. GENERATE EXECUTIVE SUMMARY
# ============================================================================

print("5. Generating executive insights...")

def generate_executive_insights(category_impact_df, feature_importance, data):
    """Generate management-ready insights"""
    
    insights = []
    
    # Top driver
    top_category = category_impact_df.iloc[0]
    insights.append({
        'type': 'PRIMARY_DRIVER',
        'title': f"🎯 Primary Churn Driver: {top_category['Category']}",
        'description': f"Accounts for {top_category['Impact']:.1%} of customer churn risk",
        'action': f"Focus immediate intervention efforts here for maximum impact"
    })
    
    # Top 3 factors
    top_3_factors = feature_importance.head(3)
    for idx, (_, factor) in enumerate(top_3_factors.iterrows(), 1):
        insights.append({
            'type': 'TOP_FACTOR',
            'title': f"#{idx} Factor: {factor['feature'].replace('_', ' ').title()}",
            'description': f"Contributes {factor['importance']:.1%} to churn probability",
            'action': f"Monitor and improve this metric across customer base"
        })
    
    # Churn rate
    churn_rate = data['churned'].mean()
    insights.append({
        'type': 'CURRENT_STATE',
        'title': f"📊 Current Churn Rate: {churn_rate:.1%}",
        'description': f"{data['churned'].sum():,} of {len(data):,} customers churned",
        'action': f"Reducing top 3 drivers could cut churn by {top_3_factors['importance'].sum():.1%}"
    })
    
    # Protective factors
    protective = feature_importance[feature_importance['feature'].isin([
        'loyalty_program', 'satisfaction_score', 'referrals_made'
    ])]
    
    if len(protective) > 0:
        insights.append({
            'type': 'OPPORTUNITY',
            'title': f"✅ Protective Factor: {protective.iloc[0]['feature'].replace('_', ' ').title()}",
            'description': f"Reduces churn risk by {protective.iloc[0]['importance']:.1%}",
            'action': f"Expand programs that drive this metric"
        })
    
    return insights

insights = generate_executive_insights(category_impact_df, feature_importance, data)

print("\n   📋 Executive Insights:\n")
for insight in insights:
    print(f"   {insight['title']}")
    print(f"      → {insight['description']}")
    print(f"      → Action: {insight['action']}\n")

# ============================================================================
# 9. SAVE SUMMARY REPORT
# ============================================================================

print("6. Saving analysis results...")

# Save feature importance
feature_importance.to_csv('/dbfs/FileStore/example_data/churn_feature_importance.csv', index=False)

# Save category impact
category_impact_df.to_csv('/dbfs/FileStore/example_data/churn_category_impact.csv', index=False)

# Save insights
insights_df = pd.DataFrame(insights)
insights_df.to_csv('/dbfs/FileStore/example_data/churn_executive_insights.csv', index=False)

print("   ✓ Analysis data saved")
print()

# ============================================================================
# 10. SUMMARY
# ============================================================================

print("=" * 80)
print("CHURN CAUSALITY ANALYSIS COMPLETE!")
print("=" * 80)
print()
print("✅ Generated Visualizations:")
print("   1. Hierarchical Causal Diagram")
print("   2. Detailed Causal Network")
print("   3. Churn Waterfall Chart")
print("   4. Sankey Flow Diagram")
print()
print("✅ Analysis Files:")
print("   - churn_feature_importance.csv")
print("   - churn_category_impact.csv")
print("   - churn_executive_insights.csv")
print()
print("📊 Key Findings:")
print(f"   • Current churn rate: {data['churned'].mean():.1%}")
print(f"   • Top churn driver: {category_impact_df.iloc[0]['Category']}")
print(f"   • #1 individual factor: {feature_importance.iloc[0]['feature']}")
print()
print("📂 Output Location: /dbfs/FileStore/example_charts/")
print("=" * 80)
