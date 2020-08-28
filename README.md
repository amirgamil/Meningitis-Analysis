# MenViz: Analyzing and Forecasting Meningitis Outbreaks
The African meningitis belt is a group of 26 countries that is acutely susceptible to meninigitis outbreaks, which can spread out of control and has killed hundreds of thousands of people. We present a dataset with more than 16 years of report information from the [World Health Organization](https://www.who.int/emergencies/diseases/meningitis/epidemiological/en/) (more information about the dataset can be found below) as well as a novel forecasting pipeline + symbolic NLU framework for extracting key details. 

### Results
Below are sample results for different countries. The y-axis represents the number of cases and the x-axis represents time where each datapoint is spaced one month apart - notice that the pipeline is robust to different patterns.
![](supporting_files/result_1.png)

### Pipeline
The pipeline is divided into two stages
1. Symbolically extracting details for each country from WHO reports as shown below
![](supporting_files/nlp.png)
2. Combine this information with the previous number of cases at $$x_{i}$$ timesteps to predict the number of cases at the $$x_{i+1}$$ timestep in the following algorithm
![](supporting_files/algorithm.png)

### Dataset Information
Note, the dataset which can be found ![here](Current_Data/data2005to2019.csv) contains 5 columns: Date, Cases, Deaths, and Summary.
The dataset was collected from weekly/monthly reports published by the World Health Organization that can be found [here](https://www.who.int/emergencies/diseases/meningitis/epidemiological/en/). Each report contains two key bits of information:
1. A table with the number of recorded cases and deaths for each country across a specific timespan (in this case 1 week). We use this table to record individual rows in our dataset
![](supporting_files/report_1). 
2. A section titled comments containing specific insights for countries that mentions region-specific details. It may mention the attack rate (AR) of specific regions within a country that were particularly high for example
![](supporting_files/report_2)

For each report, we fill rows in our dataset with the number of cases, deaths, and any relevant country-specific details from the comments in the Summary column. Note, for the date we follw this convention for consistency:
- If the report spans one week, we record the date as the first day in the range. For example, given January 3 - January 10, we would record January 3 as the date for the information from the table
- If the report spans greater than one week (usually around a month), we record the date as the midpoint of the range




