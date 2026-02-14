# ============================================================================
# CUSTOMER CHURN CAUSALITY ANALYSIS - R VERSION
# ============================================================================
# Purpose: Causal analysis of customer churn with executive-ready visuals
# Output: Causal diagrams and insights for management
# ============================================================================

library(dplyr)
library(ggplot2)
library(tidyr)
library(randomForest)
library(igraph)
library(ggraph)
library(scales)

cat("=================================================================\n")
cat("CUSTOMER CHURN CAUSALITY ANALYSIS (R)\n")
cat("=================================================================\n\n")

# ============================================================================
# 1. CREATE REALISTIC CUSTOMER CHURN DATA
# ============================================================================

cat("1. Generating customer churn data...\n")

set.seed(42)
n_customers <- 5000

# Create realistic customer data
data <- data.frame(
  customer_id = 1:n_customers,
  
  # Demographics
  customer_age = pmin(pmax(rnorm(n_customers, 45, 15), 18), 80),
  tenure_months = pmin(pmax(rexp(n_customers, 1/24), 1), 120),
  
  # Service quality
  service_calls = rpois(n_customers, 3),
  avg_call_duration = rgamma(n_customers, 2, 0.2),
  complaint_count = rpois(n_customers, 1.5),
  
  # Usage patterns
  monthly_usage_gb = rgamma(n_customers, 5, 0.1),
  login_frequency = rpois(n_customers, 15),
  feature_adoption_score = rbeta(n_customers, 2, 5) * 100,
  
  # Financial factors
  monthly_charges = pmin(pmax(rnorm(n_customers, 75, 25), 20), 200),
  total_charges = pmin(pmax(rnorm(n_customers, 1800, 1200), 0), 10000),
  payment_delays = rpois(n_customers, 0.8),
  
  # Engagement
  loyalty_program = sample(c(0, 1), n_customers, replace = TRUE, prob = c(0.6, 0.4)),
  referrals_made = rpois(n_customers, 0.5),
  satisfaction_score = rbeta(n_customers, 5, 2) * 10
)

# Create causal churn
churn_probability <- (
  0.15 * (data$monthly_charges > 100) +
  0.12 * (data$complaint_count > 2) +
  0.08 * (data$service_calls > 5) +
  0.10 * (data$login_frequency < 5) +
  0.08 * (data$feature_adoption_score < 30) +
  0.10 * (data$payment_delays > 1) +
  0.08 * (data$tenure_months < 6) +
  -0.12 * data$loyalty_program +
  -0.08 * (data$referrals_made > 0) +
  -0.10 * (data$satisfaction_score > 8) +
  0.15
)

churn_probability <- pmin(pmax(churn_probability, 0), 1)
data$churned <- as.integer(runif(n_customers) < churn_probability)

cat("   ✓ Generated", format(n_customers, big.mark = ","), "customer records\n")
cat("   ✓ Churn rate:", sprintf("%.1f%%", mean(data$churned) * 100), "\n\n")

# ============================================================================
# 2. CALCULATE FEATURE IMPORTANCE
# ============================================================================

cat("2. Analyzing causal relationships...\n")

# Prepare data for Random Forest
features <- data %>% select(-customer_id, -churned)
target <- as.factor(data$churned)

# Train Random Forest
rf_model <- randomForest(
  x = features,
  y = target,
  ntree = 100,
  importance = TRUE
)

# Get feature importance
feature_importance <- data.frame(
  feature = rownames(importance(rf_model)),
  importance = importance(rf_model)[, "MeanDecreaseGini"]
) %>%
  arrange(desc(importance)) %>%
  mutate(importance = importance / sum(importance))

cat("   Top 10 Churn Drivers:\n")
print(feature_importance %>% head(10) %>% 
        mutate(importance = sprintf("%.4f", importance)))
cat("\n")

# ============================================================================
# 3. CREATE CAUSAL CATEGORIES
# ============================================================================

cat("3. Categorizing causal factors...\n")

causal_categories <- list(
  `Financial Stress` = list(
    factors = c("monthly_charges", "total_charges", "payment_delays"),
    color = "#e74c3c",
    icon = "💰"
  ),
  `Service Quality` = list(
    factors = c("service_calls", "complaint_count", "avg_call_duration"),
    color = "#f39c12",
    icon = "📞"
  ),
  `Low Engagement` = list(
    factors = c("login_frequency", "feature_adoption_score", "monthly_usage_gb"),
    color = "#3498db",
    icon = "📊"
  ),
  `Customer Tenure` = list(
    factors = c("tenure_months", "customer_age"),
    color = "#9b59b6",
    icon = "⏱️"
  ),
  `Loyalty & Satisfaction` = list(
    factors = c("loyalty_program", "referrals_made", "satisfaction_score"),
    color = "#27ae60",
    icon = "⭐"
  )
)

# Calculate category impact
category_impact <- data.frame()
for (cat_name in names(causal_categories)) {
  cat_factors <- causal_categories[[cat_name]]$factors
  impact <- sum(feature_importance$importance[feature_importance$feature %in% cat_factors])
  
  category_impact <- rbind(category_impact, data.frame(
    Category = cat_name,
    Impact = impact,
    Color = causal_categories[[cat_name]]$color,
    Icon = causal_categories[[cat_name]]$icon
  ))
}

category_impact <- category_impact %>% arrange(desc(Impact))

cat("   Causal Category Impact:\n")
for (i in 1:nrow(category_impact)) {
  cat(sprintf("      %s %-30s %.4f\n", 
              category_impact$Icon[i],
              category_impact$Category[i],
              category_impact$Impact[i]))
}
cat("\n")

# ============================================================================
# 4. CREATE CAUSAL VISUALIZATIONS
# ============================================================================

cat("4. Creating causal diagrams...\n\n")

# Create output directory
system("mkdir -p /dbfs/FileStore/example_charts_r", ignore.stdout = TRUE)

# --------------------------------------------------------------------------
# CHART 1: Feature Importance Bar Chart
# --------------------------------------------------------------------------
cat("   a) Creating feature importance chart...\n")

top_features <- feature_importance %>% head(12)

p1 <- ggplot(top_features, aes(x = reorder(feature, importance), y = importance)) +
  geom_bar(stat = "identity", fill = "#3498db", alpha = 0.8) +
  geom_text(aes(label = sprintf("%.1f%%", importance * 100)),
            hjust = -0.2, size = 4, fontface = "bold") +
  coord_flip() +
  scale_y_continuous(labels = percent_format(), 
                     limits = c(0, max(top_features$importance) * 1.15),
                     expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Top 12 Churn Drivers by Causal Strength",
    subtitle = "Factors with highest impact on customer churn",
    x = NULL,
    y = "Causal Impact (%)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(size = 18, face = "bold", color = "#2c3e50"),
    plot.subtitle = element_text(size = 12, color = "#7f8c8d"),
    axis.text.y = element_text(size = 11, face = "bold"),
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(20, 40, 20, 20)
  )

ggsave("/dbfs/FileStore/example_charts_r/churn_feature_importance.png", 
       p1, width = 12, height = 8, dpi = 150, bg = "white")

cat("      ✓ Saved: churn_feature_importance.png\n")

# --------------------------------------------------------------------------
# CHART 2: Category Impact Comparison
# --------------------------------------------------------------------------
cat("   b) Creating category impact chart...\n")

p2 <- ggplot(category_impact, aes(x = reorder(Category, Impact), y = Impact)) +
  geom_bar(stat = "identity", aes(fill = Category), alpha = 0.85, width = 0.7) +
  geom_text(aes(label = sprintf("%s\n%.1f%%", Icon, Impact * 100)),
            hjust = -0.1, size = 5, fontface = "bold", color = "#2c3e50") +
  scale_fill_manual(values = setNames(category_impact$Color, category_impact$Category)) +
  coord_flip() +
  scale_y_continuous(labels = percent_format(),
                     limits = c(0, max(category_impact$Impact) * 1.2),
                     expand = expansion(mult = c(0, 0.05))) +
  labs(
    title = "Churn Causality by Category",
    subtitle = "Which types of factors drive customers to leave?",
    x = NULL,
    y = "Total Category Impact (%)"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(size = 18, face = "bold", color = "#2c3e50"),
    plot.subtitle = element_text(size = 12, color = "#7f8c8d"),
    axis.text.y = element_text(size = 13, face = "bold"),
    legend.position = "none",
    panel.grid.major.y = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(20, 40, 20, 20)
  )

ggsave("/dbfs/FileStore/example_charts_r/churn_category_impact.png",
       p2, width = 12, height = 7, dpi = 150, bg = "white")

cat("      ✓ Saved: churn_category_impact.png\n")

# --------------------------------------------------------------------------
# CHART 3: Network Diagram (using igraph)
# --------------------------------------------------------------------------
cat("   c) Creating causal network diagram...\n")

# Create network
edges <- feature_importance %>%
  head(10) %>%
  mutate(from = feature, to = "CHURN") %>%
  select(from, to, importance)

graph <- graph_from_data_frame(edges, directed = TRUE)

# Assign categories to nodes
V(graph)$category <- sapply(V(graph)$name, function(node) {
  if (node == "CHURN") return("Outcome")
  
  for (cat_name in names(causal_categories)) {
    if (node %in% causal_categories[[cat_name]]$factors) {
      return(cat_name)
    }
  }
  return("Other")
})

# Assign colors
V(graph)$color <- sapply(V(graph)$category, function(cat) {
  if (cat == "Outcome") return("#e74c3c")
  
  for (cat_name in names(causal_categories)) {
    if (cat == cat_name) {
      return(causal_categories[[cat_name]]$color)
    }
  }
  return("#95a5a6")
})

# Node sizes
V(graph)$size <- ifelse(V(graph)$name == "CHURN", 20, 
                       sapply(V(graph)$name, function(n) {
                         imp <- feature_importance$importance[feature_importance$feature == n]
                         if (length(imp) == 0) return(5)
                         return(5 + imp * 100)
                       }))

# Plot
png("/dbfs/FileStore/example_charts_r/churn_network_graph.png", 
    width = 1400, height = 1000, res = 150, bg = "white")

par(mar = c(1, 1, 3, 1))

plot(graph,
     vertex.color = V(graph)$color,
     vertex.size = V(graph)$size,
     vertex.label.color = "white",
     vertex.label.cex = 0.8,
     vertex.label.font = 2,
     vertex.frame.color = "white",
     edge.arrow.size = 1,
     edge.width = E(graph)$importance * 30,
     edge.color = adjustcolor("#34495e", alpha = 0.5),
     layout = layout_with_fr(graph),
     main = "Causal Network: Top Churn Drivers\n(Node size = causal strength)",
     cex.main = 1.5,
     col.main = "#2c3e50")

# Add legend
legend("bottomleft",
       legend = unique(category_impact$Category),
       fill = unique(category_impact$Color),
       border = "white",
       bty = "n",
       cex = 0.9)

dev.off()

cat("      ✓ Saved: churn_network_graph.png\n")

# --------------------------------------------------------------------------
# CHART 4: Treemap of Causal Factors
# --------------------------------------------------------------------------
cat("   d) Creating causal treemap...\n")

# Prepare data for treemap
treemap_data <- feature_importance %>%
  head(12) %>%
  mutate(
    category = sapply(feature, function(f) {
      for (cat_name in names(causal_categories)) {
        if (f %in% causal_categories[[cat_name]]$factors) {
          return(cat_name)
        }
      }
      return("Other")
    })
  ) %>%
  mutate(
    color = sapply(category, function(cat) {
      for (cat_name in names(causal_categories)) {
        if (cat == cat_name) {
          return(causal_categories[[cat_name]]$color)
        }
      }
      return("#95a5a6")
    })
  )

p4 <- ggplot(treemap_data, aes(area = importance, 
                                fill = category,
                                label = paste0(gsub("_", "\n", feature), "\n", 
                                             sprintf("%.1f%%", importance * 100)))) +
  geom_treemap(color = "white", size = 3) +
  geom_treemap_text(color = "white", place = "centre", 
                    size = 12, fontface = "bold") +
  scale_fill_manual(values = setNames(unique(treemap_data$color), 
                                     unique(treemap_data$category))) +
  labs(
    title = "Churn Causality Treemap",
    subtitle = "Size represents causal strength | Color represents category",
    fill = "Category"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(size = 18, face = "bold", color = "#2c3e50", hjust = 0.5),
    plot.subtitle = element_text(size = 12, color = "#7f8c8d", hjust = 0.5),
    legend.position = "bottom",
    legend.title = element_text(size = 12, face = "bold"),
    plot.margin = margin(20, 20, 20, 20)
  )

# Note: treemapify package needed
if (require(treemapify, quietly = TRUE)) {
  ggsave("/dbfs/FileStore/example_charts_r/churn_treemap.png",
         p4, width = 12, height = 9, dpi = 150, bg = "white")
  cat("      ✓ Saved: churn_treemap.png\n")
} else {
  cat("      ⚠ Skipping treemap (treemapify package not available)\n")
}

cat("\n")

# ============================================================================
# 5. SAVE ANALYSIS DATA
# ============================================================================

cat("5. Saving analysis results...\n")

write.csv(feature_importance, 
          "/dbfs/FileStore/example_data/churn_feature_importance_r.csv",
          row.names = FALSE)

write.csv(category_impact,
          "/dbfs/FileStore/example_data/churn_category_impact_r.csv",
          row.names = FALSE)

cat("   ✓ Analysis data saved\n\n")

# ============================================================================
# 6. GENERATE EXECUTIVE INSIGHTS
# ============================================================================

cat("6. Executive Insights:\n\n")

# Top driver
top_category <- category_impact[1, ]
cat("   🎯 PRIMARY CHURN DRIVER:\n")
cat("      ", top_category$Icon, top_category$Category, "\n")
cat("       Accounts for", sprintf("%.1f%%", top_category$Impact * 100), 
    "of customer churn risk\n")
cat("       → Action: Focus immediate intervention efforts here\n\n")

# Top 3 factors
cat("   📊 TOP 3 CAUSAL FACTORS:\n")
for (i in 1:3) {
  factor <- feature_importance[i, ]
  cat("      #", i, ":", gsub("_", " ", factor$feature), "\n")
  cat("          Impact:", sprintf("%.1f%%", factor$importance * 100), "\n")
  cat("          → Action: Monitor and improve this metric\n\n")
}

# Current state
churn_rate <- mean(data$churned)
cat("   📈 CURRENT STATE:\n")
cat("       Churn Rate:", sprintf("%.1f%%", churn_rate * 100), "\n")
cat("       Churned Customers:", format(sum(data$churned), big.mark = ","), 
    "of", format(nrow(data), big.mark = ","), "\n")
cat("       → Opportunity: Reducing top 3 drivers could cut churn by",
    sprintf("%.1f%%", sum(feature_importance$importance[1:3]) * 100), "\n\n")

# ============================================================================
# 7. SUMMARY
# ============================================================================

cat("=================================================================\n")
cat("CHURN CAUSALITY ANALYSIS COMPLETE!\n")
cat("=================================================================\n\n")

cat("✅ Generated Visualizations:\n")
cat("   1. Feature Importance Bar Chart\n")
cat("   2. Category Impact Comparison\n")
cat("   3. Causal Network Diagram\n")
cat("   4. Causal Treemap (if available)\n\n")

cat("✅ Analysis Files:\n")
cat("   - churn_feature_importance_r.csv\n")
cat("   - churn_category_impact_r.csv\n\n")

cat("📊 Key Findings:\n")
cat("   • Current churn rate:", sprintf("%.1f%%", churn_rate * 100), "\n")
cat("   • Top churn driver:", as.character(category_impact$Category[1]), "\n")
cat("   • #1 individual factor:", as.character(feature_importance$feature[1]), "\n\n")

cat("📂 Output Location: /dbfs/FileStore/example_charts_r/\n")
cat("=================================================================\n")
