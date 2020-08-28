# MenViz: Analyzing and Forecasting Meningitis Outbreaks
The African meningitis belt is a group of 26 countries that is acutely susceptible to meninigitis outbreaks, which can spread out of control and has killed hundreds of thousands of people. We present a dataset with more than 16 years of report information from the World Health Organization as well as a novel forecasting pipeline + symbolic NLU framework for extracting key details. 

Below are sample results for different countries - notice that the pipeline is robust to different patterns.

The pipeline is divided into stages
1. Symbolically extracting details for each country from WHO reports as shown below
2. Combine this information with the previous number of cases at $x$ timesteps to predict the number of cases at the $x_{n+1}$ timestep in the following algorithm

[]
