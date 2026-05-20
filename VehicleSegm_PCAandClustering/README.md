# Vehicle Segmentation — PCA and Clustering

This was a personal learning project to get hands-on practice with PCA and unsupervised clustering. The dataset used is the classic Auto MPG dataset, and the goal was to group vehicles by their specs using dimensionality reduction followed by two clustering methods.

---

## What it covers

- **EDA** — correlation matrix, scatter matrix, VIF analysis to understand multicollinearity
- **PCA** — standardized features, reduced to 3 components (90%+ cumulative variance), scree plot
- **K-Means** — elbow method to pick k=3, clusters visualized on PC1 vs PC2
- **Hierarchical Clustering** — Ward linkage, dendrogram, cut at 3 clusters
- **Comparison** — Adjusted Rand Index of 0.907, meaning both methods produced nearly identical groupings

## Results

Three natural vehicle segments emerged from both methods:

- **Heavy/powerful** — 8 cylinders, high displacement, low MPG, older models
- **Mid-range** — average performance across all features
- **Efficient/light** — 4 cylinders, high MPG, newer models

---

## Stack

`pandas` `numpy` `scikit-learn` `scipy` `seaborn` `matplotlib` `plotly`

---

## Dataset

[Auto MPG — UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/9/auto+mpg)
