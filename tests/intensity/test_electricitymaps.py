import unittest
from unittest.mock import patch, MagicMock
from carbontracker.emissions.intensity.fetchers.electricitymaps import ElectricityMap
from carbontracker import exceptions

class TestElectricityMap(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.electricity_map = ElectricityMap(logger=self.logger, api_key="test_key")
        self.g_location = MagicMock()
        self.g_location.lng = 0.0
        self.g_location.lat = 0.0
        self.g_location.country = "US"

    def test_set_api_key(self):
        self.assertEqual(self.electricity_map._api_key, "test_key")

    def test_suitable(self):
        self.assertTrue(self.electricity_map.suitable(self.g_location))

    @patch("requests.get")
    def test_carbon_intensity_by_location_with_lon_lat(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"carbonIntensity": 50.0}
        mock_get.return_value = mock_response

        result = self.electricity_map._carbon_intensity_by_location(lon=self.g_location.lng, lat=self.g_location.lat)
        self.assertEqual(result, 50.0)

    @patch("requests.get")
    def test_carbon_intensity_by_location_with_zone(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"carbonIntensity": 75.0}
        mock_get.return_value = mock_response

        result = self.electricity_map._carbon_intensity_by_location(zone=self.g_location.country)
        self.assertEqual(result, 75.0)

    @patch("requests.get")
    def test_carbon_intensity_by_location_bad_json_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.json.return_value = ""
        mock_get.return_value = mock_response

        with self.assertRaises(exceptions.CarbonIntensityFetcherError):
            self.electricity_map._carbon_intensity_by_location(lon=self.g_location.lng, lat=self.g_location.lat)

    @patch("requests.get")
    def test_carbon_intensity_by_location_json_response_not_ok(self, mock_get):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.json.return_value = {"error": "some error"}
        mock_get.return_value = mock_response

        with self.assertRaises(exceptions.CarbonIntensityFetcherError):
            self.electricity_map._carbon_intensity_by_location(lon=self.g_location.lng, lat=self.g_location.lat)
    

    @patch.object(ElectricityMap, "_carbon_intensity_by_location")
    def test_carbon_intensity(self, mock_carbon_intensity_by_location):
        mock_carbon_intensity_by_location.return_value = 100.0

        intensity_fetch = self.electricity_map.fetch_carbon_intensity(self.g_location)

        self.assertEqual(intensity_fetch.carbon_intensity, 100.0)

    @patch.object(ElectricityMap, "_carbon_intensity_by_location")
    def test_carbon_intensity_with_exception(self, mock_carbon_intensity_by_location):
        mock_carbon_intensity_by_location.side_effect = [Exception(), 25.0]

        intensity_fetch = self.electricity_map.fetch_carbon_intensity(self.g_location)

        mock_carbon_intensity_by_location.assert_called_with(zone=self.g_location.country)
        self.assertEqual(intensity_fetch.carbon_intensity, 25.0)



if __name__ == "__main__":
    unittest.main()
