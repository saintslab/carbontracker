from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

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
    def carbon_intensity(self, g_location, time_dur=None):
        """
        Returns the carbon intensity by location and duration (s).
        If the API supports predicted intensities time_dur can be used.
        """
        raise NotImplementedError

