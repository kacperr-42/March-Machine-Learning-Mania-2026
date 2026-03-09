setwd('/home/joziop/Documents/Projekt Interdyscyplinarny/March-Machine-Learning-Mania-2026')
path <- "data/"

files <- list.files(path = path, pattern = "\\.csv$", full.names = TRUE)

data_list <- lapply(files, read.csv)

names(data_list) <- gsub(".csv", "", basename(files))

data_list$MTeams
data_list$Cities

m_tourney = data_list$MNCAATourneyDetailedResults
w_tourney = data_list$WNCAATourneyDetailedResults
m_seeds = data_list$MNCAATourneySeeds
w_seeds = data_list$WNCAATourneySeeds
m_regular = data_list$MRegularSeasonDetailedResults
w_regular = data_list$WRegularSeasonDetailedResults


library(dplyr)
m_tourney$isTourney = 1
m_regular$isTourney = 0

m_tourney_regular <- rbind(m_tourney, m_regular)


m_data <- m_tourney_regular %>%
  left_join(m_seeds, by = c("Season", "WTeamID" = "TeamID")) %>% 
  rename(WSeed = Seed) %>% 
  left_join(m_seeds, by = c("Season", "LTeamID" = "TeamID")) %>% 
  rename(LSeed = Seed) %>% 
  mutate(
    WSeed = ifelse(isTourney == 1, WSeed, NA_integer_),
    LSeed = ifelse(isTourney == 1, LSeed, NA_integer_)
  )

w_tourney$isTourney = 1
w_regular$isTourney = 0

w_tourney_regular <- rbind(w_tourney, w_regular)


w_data <- w_tourney_regular %>%
  left_join(w_seeds, by = c("Season", "WTeamID" = "TeamID")) %>% 
  rename(WSeed = Seed) %>% 
  left_join(w_seeds, by = c("Season", "LTeamID" = "TeamID")) %>% 
  rename(LSeed = Seed) %>% 
  mutate(
    WSeed = ifelse(isTourney == 1, WSeed, NA_integer_),
    LSeed = ifelse(isTourney == 1, LSeed, NA_integer_)
  )

write.csv(w_data, "w_data.csv", row.names = FALSE)
write.csv(m_data, "m_data.csv", row.names = FALSE)
