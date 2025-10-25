# 🧪 Laboratory Safety Project  
**AI-Driven Analysis and Risk Prediction for Laboratory Incidents**

---

## Overview
The **Laboratory Safety Project** applies **data analytics and machine learning** to real-world laboratory incident reports.  
The goal is to identify patterns in safety failures, understand root causes, and develop predictive models that classify the **severity of incidents** into three levels:
- 🟢 **Low** — Near misses or minor injuries  
- 🟡 **Medium** — Incidents requiring medical attention  
- 🔴 **High** — Severe injuries, explosions, or fatalities  

By combining structured data (causes, damages, lessons learned) with intelligent models, this project helps build **proactive safety monitoring systems** for laboratories.

---

## Objectives
- Perform **Exploratory Data Analysis (EDA)** to discover trends and correlations in laboratory incidents.  
- Visualize **root causes**, **human injuries**, and **lab damage types** using interactive Plotly charts.  
- Build machine learning models to **predict severity level** based on categorical features.  
- Develop a foundation for future **Computer Vision + Alert Systems** that detect unsafe lab behavior (e.g., no PPE, spills, fire).

---

## Dataset Description
**Dataset Name:** Academic Laboratory Safety Incidents Dataset  
**Records:** 150 laboratory incidents  
**Columns:** 11 (descriptive + categorical)  

| Column | Description |
|---------|-------------|
| `incident_id` | Unique identifier for each incident |
| `people_involved_type` | Type/number of people involved |
| `damage_human` | Injury type (burn, cut, inhalation, etc.) |
| `damage_lab` | Lab/equipment/environmental damage type |
| `severity` | Original 5-level impact classification |
| `chemicals` | Chemicals involved in the incident |
| `cause` | Root cause(s) (human error, equipment failure, etc.) |
| `narrative_description` | Short factual summary of the incident |
| `lessons_learned` | Safety takeaway(s) |
| `university` | University name where it occurred |
| `source_URL` | Link to source report |

**Severity Grouping (for modeling):**
| New Class | Original Labels | Meaning |
|------------|----------------|----------|
| **Low** | near miss, minor | Minor or no injuries |
| **Medium** | moderate | Medical treatment required |
| **High** | major, severe | Serious injury, explosion, or fatality |

---

## Exploratory Data Analysis (EDA)
EDA was performed using **Plotly Express** for interactive visualizations.

### Key Questions & Insights:
1. **What are the most common root causes?**  
   → *Human error* accounts for 80% of incidents.  
2. **Which injuries occur most often?**  
   → *Burns and cuts* dominate human injuries.  
3. **What types of lab damage are frequent?**  
   → *Fire, chemical release, and contamination* are most frequent.  
4. **How does severity distribute across incidents?**  
   → Majority are *moderate* or *major* severity.

 **Interactive Charts Created:**
- Severity distribution  
- Root cause grouping  
- Injury vs. lab damage heatmap  
- PPE-related severity comparison  

---

## Machine Learning Modeling

### Models Compared:
| Model | Type | Description |
|--------|------|-------------|
| Decision Tree | Baseline | Simple, interpretable model |
| Random Forest | Ensemble | Robust classifier with feature averaging |
| XGBoost | Gradient Boosted | Handles imbalance and complex relations |
| CatBoost | Gradient Boosted | Optimized for categorical data |

### Training Pipeline:
1. Preprocessing with `OneHotEncoder` (for all categorical features).  
2. Split into training/testing (80/20).  
3. Stratified sampling to balance classes.  
4. GridSearchCV for hyperparameter optimization.  
5. Evaluation using Accuracy + Weighted F1-Score.

---




git clone https://github.com/MUSAB10000/Laboratory_Safety_Project.git
cd Laboratory_Safety_Project
