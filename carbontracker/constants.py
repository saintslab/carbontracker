# Power Usage Effectiveness Coefficient.
# Rhonda Ascierto. 2020-2021. Uptime Institute Annual Data Center Survey.
# https://www.missioncriticalmagazine.com/ext/resources/whitepapers/2020/2020AnnualSurvey_EndUser_v4s.pdf
from carbontracker.emissions.intensity.fetchers import electricitymaps


PUE_2020 = 1.59

# https://uptimeinstitute.com/2021-data-center-industry-survey-results
PUE_2021 = 1.57

# https://uptimeinstitute.com/uptime_assets/6768eca6a75d792c8eeede827d76de0d0380dee6b5ced20fde45787dd3688bfe-2022-data-center-industry-survey-en.pdf
PUE_2022 = 1.55

# https://journal.uptimeinstitute.com/global-pues-are-they-going-anywhere/
PUE_2023 = 1.58

# World-wide average carbon intensity of electricity production in 2019.
# https://www.iea.org/reports/global-energy-co2-status-report-2019/emissions
# 2025 update: Now uses number from https://www.iea.org/reports/electricity-2025/emissions
WORLD_AVG_CARBON_INTENSITY = 445
WORLD_AVG_CARBON_INTENSITY_YEAR = 2024


