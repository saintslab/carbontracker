import geocoder
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
import sys

from carbontracker import constants
from carbontracker.emissions.intensity import intensity

from carbontracker.emissions.intensity.intensity import IntensityFetch, IntensityService 

class TestIntensity(unittest.TestCase):
    @patch("geocoder.ip")
    def test_get_default_intensity_success(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Sample Address"
        mock_location.country = "US"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        default_intensity_fetch = service.default_carbon_intensity

        # importlib.resources.files was introduced in Python 3.9 and replaces deprecated pkg_resource.resources
        if sys.version_info < (3,9):
            import pkg_resources
            carbon_intensities_df = pd.read_csv(pkg_resources.resource_filename("carbontracker", "data/carbon-intensities.csv"))
        else:
            import importlib.resources
            ref = importlib.resources.files("carbontracker") / "data/carbon-intensities.csv"
            with importlib.resources.as_file(ref) as path:
                carbon_intensities_df = pd.read_csv(path)
        intensity_row = carbon_intensities_df[carbon_intensities_df["alpha-2"] == mock_location.country].iloc[0]
        expected_intensity = intensity_row["Carbon intensity of electricity (gCO2eq/kWh)"]

        self.assertEqual(default_intensity_fetch.carbon_intensity, expected_intensity)
        self.assertIn("Defaulted to average carbon intensity", service.generate_logging_message(carbon_intensity_fetch=default_intensity_fetch))

    @patch("geocoder.ip")
    def test_get_default_intensity_location_failure(self, mock_geocoder_ip):
        mock_geocoder_ip.return_value.ok = False

        service = IntensityService(logger=Mock())
        default_intensity_fetch = service.default_carbon_intensity

        self.assertEqual(default_intensity_fetch.carbon_intensity, constants.WORLD_AVG_CARBON_INTENSITY)
        self.assertIn("Defaulted to average global carbon intensity", service.generate_logging_message(carbon_intensity_fetch=default_intensity_fetch))

    @patch("geocoder.ip")
    @patch("pandas.read_csv")
    def test_get_default_intensity_data_file_failure(
            self, mock_read_csv, mock_geocoder_ip
    ):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Sample Address"
        mock_location.country = "US"
        mock_geocoder_ip.return_value = mock_location

        mock_read_csv.side_effect = FileNotFoundError
        
        logger = MagicMock()
        intensity_service = IntensityService(logger) 
        default_intensity = intensity_service.default_carbon_intensity  


        expected_description = (
            f"Live carbon intensity could not be fetched at detected location: {mock_location.address}. "
            f"Defaulted to average global carbon intensity: {constants.WORLD_AVG_CARBON_INTENSITY:.2f} gCO2eq/kWh ({constants.WORLD_AVG_CARBON_INTENSITY_YEAR})."
        )

        assert default_intensity.carbon_intensity == constants.WORLD_AVG_CARBON_INTENSITY
        assert intensity_service.generate_logging_message(default_intensity) == expected_description

    @patch("geocoder.ip")
    def test_get_default_intensity_ip_location_failure(self, mock_geocoder_ip):
        mock_geocoder_ip.return_value.ok = False
        
        
        logger = MagicMock()
        intensity_service = IntensityService(logger) 
        default_intensity = intensity_service.default_carbon_intensity  

        self.assertEqual(default_intensity.carbon_intensity, constants.WORLD_AVG_CARBON_INTENSITY)
        self.assertIn("Defaulted to average global carbon intensity",intensity_service.generate_logging_message(default_intensity)) 

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_localized_fallback(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Aarhus, Capital Region, DK"
        mock_location.country = "DK"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        default_fetch = service.default_carbon_intensity

        expected_message = (
            f"Defaulted to average carbon intensity for {default_fetch.country}: "
            f"{default_fetch.carbon_intensity:.2f} gCO2eq/kWh."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=default_fetch),
            expected_message,
        )

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_global_fallback(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = False
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        default_fetch = service.default_carbon_intensity

        expected_message = (
            f"Live carbon intensity could not be fetched at detected location: Unknown. "
            f"Defaulted to average global carbon intensity: "
            f"{constants.WORLD_AVG_CARBON_INTENSITY:.2f} gCO2eq/kWh ({constants.WORLD_AVG_CARBON_INTENSITY_YEAR})."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=default_fetch),
            expected_message,
        )

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_prediction_with_duration(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Copenhagen, DK"
        mock_location.country = "DK"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        forecast_fetch = IntensityFetch(
            carbon_intensity=123.456,
            address=service.address,
            country=service.country,
            is_fetched=True,
            is_localized=True,
            is_prediction=True,
            time_duration=3600,
        )

        expected_message = (
            "Forecasted carbon intensity for the next 1:00:00: "
            f"{forecast_fetch.carbon_intensity:.2f} gCO2eq/kWh."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=forecast_fetch),
            expected_message,
        )

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_prediction_without_duration(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Copenhagen, DK"
        mock_location.country = "DK"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        forecast_fetch = IntensityFetch(
            carbon_intensity=98.7,
            address=service.address,
            country=service.country,
            is_fetched=True,
            is_localized=True,
            is_prediction=True,
        )

        expected_message = (
            f"Forecasted carbon intensity: {forecast_fetch.carbon_intensity:.2f} gCO2eq/kWh."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=forecast_fetch),
            expected_message,
        )

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_prediction_fallback_with_duration(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Copenhagen, DK"
        mock_location.country = "DK"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        fallback_fetch = IntensityFetch(
            carbon_intensity=service.default_carbon_intensity.carbon_intensity,
            address=service.address,
            country=service.country,
            is_fetched=False,
            is_localized=True,
            is_prediction=True,
            time_duration=7200,
        )

        expected_message = (
            "Failed to predict carbon intensity for the next 2:00:00, fallback on average measured intensity "
            f"at detected location: {service.address}."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=fallback_fetch),
            expected_message,
        )

    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_generate_logging_message_prediction_fallback_without_duration(self, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = "Copenhagen, DK"
        mock_location.country = "DK"
        mock_geocoder_ip.return_value = mock_location

        service = IntensityService(logger=Mock())
        fallback_fetch = IntensityFetch(
            carbon_intensity=service.default_carbon_intensity.carbon_intensity,
            address=service.address,
            country=service.country,
            is_fetched=False,
            is_localized=True,
            is_prediction=True,
        )

        expected_message = (
            "Failed to predict carbon intensity, fallback on average measured intensity "
            f"at detected location: {service.address}."
        )

        self.assertEqual(
            service.generate_logging_message(carbon_intensity_fetch=fallback_fetch),
            expected_message,
        )

    @patch("geocoder.ip")
    def test_carbon_intensity_location_failure(self, mock_geocoder_ip):
        mock_geocoder_ip.return_value.ok = False

        logger = MagicMock()

        intensity_service = IntensityService(logger) 
        default_intensity = intensity_service.default_carbon_intensity  
        self.assertEqual(default_intensity.carbon_intensity, constants.WORLD_AVG_CARBON_INTENSITY)
        self.assertEqual(default_intensity.address, "Unknown")
        self.assertEqual(default_intensity.is_fetched, False)
        self.assertEqual(default_intensity.is_localized, False)
        self.assertEqual(default_intensity.is_prediction, False)
        self.assertIn("Defaulted to average global carbon intensity: ", intensity_service.generate_logging_message(default_intensity) )



    @patch("geocoder.ip")
    @patch("carbontracker.emissions.intensity.fetchers.electricitymaps.ElectricityMap")
    def test_carbon_intensity_address_assignment(self, mock_electricity_map, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_location.address = None
        mock_geocoder_ip.return_value = mock_location

        mock_electricity_map.return_value.suitable.return_value = False

        
        logger = MagicMock()
        intensity_service = IntensityService(logger, intensity_fetcher=mock_electricity_map) 
        default_intensity = intensity_service.fetch_carbon_intensity("100")
 
        self.assertIsNone(default_intensity.address)
        mock_electricity_map.suitable.assert_called_once_with(mock_location)

    @patch("geocoder.ip")
    @patch("carbontracker.emissions.intensity.fetchers.electricitymaps.ElectricityMap.carbon_intensity")
    def test_carbon_intensity_failure(self, mock_electricity_map_carbon_intensity, mock_geocoder_ip):
        mock_location = MagicMock()
        mock_location.ok = True
        mock_geocoder_ip.return_value = mock_location

        mock_electricity_map_carbon_intensity.side_effect = Exception("Test Exception")

        logger = MagicMock()

        intensity_service = IntensityService(logger)
        intensity_fetch = intensity_service.fetch_carbon_intensity() 
        
        self.assertFalse(intensity_fetch.is_fetched)
        self.assertIn("could not be fetched", intensity_service.generate_logging_message(carbon_intensity_fetch=intensity_fetch))

    @patch("carbontracker.emissions.intensity.fetchers.carbonintensitygb.CarbonIntensityGB")
    @patch("carbontracker.emissions.intensity.intensity.geocoder.ip")
    def test_carbon_intensity_exception_carbonintensitygb(self, mock_geocoder, mock_carbonintensitygb):
        mock_geocoder.return_value.address = "Sample Address"
        mock_geocoder.return_value.ok = True
        mock_carbonintensitygb.return_value.suitable.return_value = True
        mock_carbonintensitygb.return_value.carbon_intensity.return_value = 23.0 

        logger = MagicMock()

        intensity_service = IntensityService(logger, mock_carbonintensitygb())

        intensity_fetch = intensity_service.fetch_carbon_intensity() 
        self.assertEqual(intensity_fetch.carbon_intensity, 23.0)
        self.assertTrue(intensity_fetch.is_fetched)

    @patch("carbontracker.emissions.intensity.fetchers.energidataservice.EnergiDataService")
    def test_carbon_intensity_energidataservice(self, mock_energidataservice):
        mock_energidataservice.return_value.suitable.return_value = True
        mock_energidataservice.return_value.carbon_intensity.return_value = 23

        logger = MagicMock()
        intensity_service = IntensityService(logger, mock_energidataservice())
        intensity_fetch = intensity_service.fetch_carbon_intensity()

        self.assertEqual(intensity_fetch.carbon_intensity, 23.0)
        self.assertTrue(intensity_fetch.is_fetched)


