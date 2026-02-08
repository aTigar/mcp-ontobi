---
# SKOS
skos:prefLabel: Information Gain
skos:definition: The reduction in entropy (uncertainty) achieved by splitting a node on a feature in decision tree construction; measures how much a particular feature decreases the overall disorder of class labels, guiding optimal split selection.
skos:broader: ["[[Decision Trees]]","[[Gini Impurity]]","[[Decision Boundary]]"]
skos:related: []

# SCHEMA.ORG
"@type": "DefinedTerm"
identifier: concept-information-gain
dateCreated: "[[03.02.2026]]"

# METADATA
aliases: []
tags: ["#concept"]
---

# Information Gain

Information gain is a key metric in decision tree algorithms that quantifies the effectiveness of a feature for classification.

## Formula

Information Gain = Entropy(parent) - Weighted Average of Entropy(children)

## Usage

- Used in ID3 and C4.5 algorithms
- Helps select the best feature to split on at each node
- Higher information gain indicates better feature for splitting
