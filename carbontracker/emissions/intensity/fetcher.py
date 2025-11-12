from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

class IntensityFetch():
    def __init__(self,carbon_intensity : float, address : str, country : str, is_fetched : bool, is_localized : bool, is_prediction = False, time_duration : Optional[int] = None ): 
        self.carbon_intensity = carbon_intensity
        self.address = address
        self.country = country
        self.is_prediction = is_prediction
        self.is_fetched = is_fetched 
        self.is_localized = is_localized 
        self.time_duration = time_duration 

class IntensityFetcher:
    __metaclass__ = ABCMeta

    def __init__(self, *, logger, api_key=None):
        self.logger = logger
        self.api_key = api_key
        
    @abstractmethod
    def suitable(self, g_location):
        """Returns True if it can be used based on geocoder location."""
        raise NotImplementedError

    @abstractmethod
    def fetch_carbon_intensity(self, g_location, time_dur=None) -> IntensityFetch:
        """
        Returns the carbon intensity by location and duration (s).
        If the API supports predicted intensities time_dur can be used.
        """
        raise NotImplementedError

