install.packages("dplyr")
library(dplyr)


library(readr)
install.packages("reshape2")
library(reshape2)



wildlife <- read_csv("wildlife.csv")

pivot_table <- dcast(wildlife, Species ~ Region.label, value.var = "Counts", sum)
print(pivot_table)
pivot_table$TotalCount <- rowSums(pivot_table[, -1], na.rm = TRUE)  # Exclude the Species column



# Count the number of rows with values > 0 for each column
count_numeric_values <- function(x) {
  if (is.numeric(x)) {
    sum(x > 0, na.rm = TRUE)
  } else {
    NA  # Non-numeric columns get NA
  }
}

# Apply function to each column
count_row <- sapply(pivot_table, count_numeric_values)
df_with_count <- rbind(pivot_table, count_row)
rownames(df_with_count)[nrow(df_with_count)] <- "Species Count"


## Calculate Simpson's diversity index using our data (rows = species, columns = land covers)
# Remove species names column, keeping only numeric counts


# Function to calculate Simpson's Index
simpsons_index <- function(counts) {
  N <- sum(counts, na.rm = TRUE)  # Total number of individuals, ignoring NA
  numerator <- sum(counts * (counts - 1), na.rm = TRUE)
  denominator <- N * (N - 1)
  D <- 1 - (numerator / denominator)
  return(D)
}

# Remove species names column, keeping only numeric counts
species_counts <- pivot_table[, 2:4]

# Apply the Simpson's Index calculation to each land cover (each column)
simpsons_indices <- apply(species_counts, 2, simpsons_index)

# Round Simpson's Index values to one decimal point
simpsons_indices <- round(simpsons_indices, 1)

# Append the Simpson's Index as a new row to the data frame
# Append the count row to the data frame


df_with_simpson <- rbind(df_with_count, c("NA", simpsons_indices))
rownames(df_with_simpson)[nrow(df_with_simpson)] <- "Simpson's Diversity Index"


# Print the final result with species and Simpson's Index at the bottom
print(df_with_simpson)



### Now Append the information from Livestock


livestock<-read_csv("livestock.csv")


pivot_livestock <- dcast(livestock, Species ~ Region.label, value.var = "Counts", sum)
print(pivot_livestock)
pivot_livestock$TotalCount <- rowSums(pivot_livestock[, -1], na.rm = TRUE)
pivot_livestock$Woodland<-as.character(pivot_livestock$Woodland)
pivot_livestock$Shrubland<-as.character(pivot_livestock$Shrubland)
pivot_livestock$TotalCount<-as.character(pivot_livestock$TotalCount)


combined_df <- full_join(df_with_simpson, pivot_livestock, by = c("Species", "Woodland", "Shrubland", "TotalCount"))


combined_df$SpeciesNames <- c("Dik dik", "Elephant", "GG?", "Giraffe", 
                         "Hyena", "Impala", "Jackal", "TG??", "Zebra", "Species Count", "Simpson's Diversity Index",
                         "Cattle", "Donkey", "Sheep and Goats")
combined_df <- combined_df[, c("SpeciesNames", "Species", "Semiarid", "Shrubland", "Woodland","Grassland", "TotalCount")]
print(combined_df)

