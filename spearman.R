### Statistical tests and summary statistics for Makuyuni Wildlife Corridor study
library(tidyverse)

# in QGIS, create a 350 meter buffer around transects
# and then calculate zonal statistics with the least cost corridor
# to find the minimum cost (best path) through each transect

# read in minimum cost (of least cost corridor)
transect_observations <- read.csv("minimum_cost.csv")

# Read in wildlife and livestock observation data
observation_data <- read_excel("observation_data.xlsx")

# summarize the counts of wild and domestic animals by transect
sum_obs <- observation_data %>% 
  select(Transect, Wild_Dom, Counts) %>% 
  group_by(Transect, Wild_Dom) %>% 
  summarise(totals = sum(Counts), .groups="drop")

# create mammals table with one row per transect, 
# wildlife counts in one column and
# livestock counts in another
livestock <- sum_obs %>% filter(Wild_Dom == "Dom") %>% select(Transect, livestock = totals)
wildlife <- sum_obs %>% filter(Wild_Dom == "Wild") %>% select(Transect, wildlife = totals)

# join wildlife and livestock counts to transect_observations
transect_observations <- transect_observations %>% 
  left_join(wildlife, by="Transect") %>% 
  left_join(livestock, by="Transect")

# fill transects with no (NA) observations with 0
transect_observations$livestock <- replace_na(transect_observations$livestock, 0)
transect_observations$wildlife <- replace_na(transect_observations$wildlife, 0)

# calculate ranks
transect_observations$lsrank <- rank(-transect_observations$livestock)
transect_observations$wirank <- rank(-transect_observations$wildlife)
transect_observations$ranksum <- transect_observations$lsrank + transect_observations$wirank

# Spearman's Rho correlation test, one-tailed
# HA: There is a negative correlation between wildlife corridor cost and observation of wildlife
corridor_test <- cor.test(transect_observations$min_corridor_cost, transect_observations$wildlife, method = "spearm", alternative = "less")
corridor_test

# S = 3144, p-value = 0.003081
# alternative hypothesis: true rho is less than 0
# sample estimates:
#   rho 
# -0.5533567 

# Filter for transects with non-zero observations
nonzero_obs <- filter(transect_observations, wildlife > 0 | livestock > 0) 

# spearman's rho correlation test, one-tailed
# HA: There is a negative correlation between number of livestock observed and number of wildlife observed
cor.test(nonzero_obs$livestock, 
         nonzero_obs$wildlife,
         method = "spearm",
         alternative = "less")

# Spearman's Rho results in comment below

# data:  mammals$livestock and mammals$wildlife
# S = 1934.6, p-value = 0.1311
# alternative hypothesis: true rho is less than 0
# sample estimates:
#        rho 
# -0.2562542 