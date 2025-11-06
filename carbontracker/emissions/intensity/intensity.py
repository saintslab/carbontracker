import sys
import pandas as pd
from carbontracker.emissions.intensity.fetchers import electricitymaps
import geocoder
import traceback
from typing import List, Optional, Tuple, Type
from carbontracker import constants, exceptions, loggerutil
from carbontracker.emissions.intensity.fetcher import IntensityFetcher
from carbontracker.emissions.intensity.location import Location

class IntensityFetch():
    def __init__(self,carbon_intensity : float, address : str, country : str, is_fetched : bool, is_localized : bool, is_prediction = False, time_duration : Optional[int] = None ): 
        self.carbon_intensity = carbon_intensity
        self.address = address
        self.country = country
        self.is_prediction = is_prediction
        self.is_fetched = is_fetched 
        self.is_localized = is_localized 
        self.time_duration = time_duration 



class IntensityService():
    def __init__(self,
                 logger : loggerutil.Logger,
                 intensity_fetcher : Optional[IntensityFetcher] = None,
                 ) -> None:
        self.logger = logger 
        self.intensity_fetcher = intensity_fetcher
        self.geo_location = self._fetch_geo_location()
        self.address = self._get_address()
        self.country = self._get_country()
        self.using_global_average = False
        self.default_carbon_intensity = self._get_default_carbon_intensity()


    def fetch_carbon_intensity(self, time_duration = None) -> IntensityFetch:
        if self.intensity_fetcher is None:
            return self.default_carbon_intensity
        else:
            if not self.intensity_fetcher.suitable(self.geo_location):
                self.logger.err_warn(
                    f"Fetcher is unable to retrieve carbon intensity data for your detected location {self.address}" 
                )
            try: 
                carbon_intensity : float = self.intensity_fetcher.carbon_intensity(g_location=self.geo_location,time_dur=time_duration)

                return IntensityFetch(
                    carbon_intensity=carbon_intensity,
                    address=self.address,
                    country=self.country,
                    is_fetched=True,
                    is_localized=True,
                    is_prediction=False,  # THis is problematic, we dont have a unified way of determining whether someting is a predict. Also currently using only the electr
                )
            except:
                self.logger.err_warn(
                    f"Could not retrieve carbon intensity data" 
                )

                return self.default_carbon_intensity
    
    def _get_default_carbon_intensity(self) -> IntensityFetch:
        """Retrieve static default carbon intensity value based on location."""
        try:
            # importlib.resources.files was introduced in Python 3.9
            if sys.version_info < (3, 9):
                import pkg_resources

                path = pkg_resources.resource_filename(
                    "carbontracker", "data/carbon-intensities.csv"
                ) # pyright: ignore[reportOptionalCall]
            else:
                import importlib.resources

                path = importlib.resources.files("carbontracker").joinpath(
                    "data", "carbon-intensities.csv" # type: ignore
                )
            carbon_intensities_df = pd.read_csv(str(path))
            intensity_row = carbon_intensities_df[
                carbon_intensities_df["alpha-2"] == self.country
            ].iloc[0]
            intensity: float = intensity_row["Carbon intensity of electricity (gCO2eq/kWh)"]
            return IntensityFetch(
                carbon_intensity=intensity,
                address=self.address,
                country=self.country,
                is_fetched=False,
                is_localized=True,
                is_prediction=False,
            )
        except Exception as err:
            self.using_global_average = True

            intensity = constants.WORLD_AVG_CARBON_INTENSITY
            self.logger.err_warn(
                f"Unable to determine average default carbon intensity for your specific location {self.address}.",
            )

            return IntensityFetch(
            carbon_intensity=intensity,
            address=self.address,
            country=self.country,
            is_localized=False,
            is_fetched=False,
            is_prediction=False,
        )
  

            
        

    def _fetch_geo_location(self) -> Optional[Location]: 
            try:
                g_location: Location = geocoder.ip("me")
            except Exception as err:
                return None
            return g_location
    
    def _get_address(self) -> str: 
        if self.geo_location is None or not self.geo_location.ok:
            return "Unknown"
        else:
            return self.geo_location.address
     
    def _get_country(self) -> str: 
        if self.geo_location is None or not self.geo_location.ok:
            return "Unknown"
        else:
            return self.geo_location.country

    def generate_logging_message(self, carbon_intensity_fetch : IntensityFetch) -> str:
        location = self.address if self.address != "Unknown" else "detected location"

        if carbon_intensity_fetch.is_prediction:
            if carbon_intensity_fetch.is_fetched:
                if carbon_intensity_fetch.time_duration is not None:
                    return (
                        "Forecasted carbon intensity for the next "
                        f"{loggerutil.convert_to_timestring(carbon_intensity_fetch.time_duration)}: "
                        f"{carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh."
                    )
                return (
                    f"Forecasted carbon intensity: {carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh."
                )
            else: 
                if carbon_intensity_fetch.time_duration is not None:
                    return f"Failed to predict carbon intensity for the next {loggerutil.convert_to_timestring(carbon_intensity_fetch.time_duration)}, fallback on average measured intensity at detected location: {self.address}."
                else: 
                    return f"Failed to predict carbon intensity, fallback on average measured intensity at detected location: {self.address}."
        if carbon_intensity_fetch.is_fetched:
            if carbon_intensity_fetch.is_localized:
                return (
                    f"Live carbon intensity fetched for {location}: "
                    f"{carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh."
                )
            
            ## This case should never happen. If is_localized false, it would have defaulted  to the global carbon intensity
            return (
                f"Live carbon intensity could not be fetched at detected location: {carbon_intensity_fetch.address}."
                f"Defaulted to average global carbon intensity: "
                f"{carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh. ({constants.WORLD_AVG_CARBON_INTENSITY_YEAR})"
            )


        if carbon_intensity_fetch.is_localized:
            return (
                f"Defaulted to average carbon intensity for {carbon_intensity_fetch.country}: "
                f"{carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh."
            )

        return (
            f"Live carbon intensity could not be fetched at detected location: {carbon_intensity_fetch.address}. "
            f"Defaulted to average global carbon intensity: "
            f"{carbon_intensity_fetch.carbon_intensity:.2f} gCO2eq/kWh ({constants.WORLD_AVG_CARBON_INTENSITY_YEAR})."
        )

