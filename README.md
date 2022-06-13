# Lux AI 2021 Challenge

This is a rule based implementation for Kaggle's Lux AI 2021 Challenge. Agents evaluate the terrain through a list of rules and
decide on what they'll do based on this information. Each rule outputs a normalized value that is then multiplied by a hyperparameter for that rule's importance,
resulting on its score. Highest score decides the agent's action.

Hyperparameters were trained initially by randomly sampling the parameter space then by sampling around the winning configuration with a configurable distance. 
Configurations fought against each other and with time I decided to decrease this value.
