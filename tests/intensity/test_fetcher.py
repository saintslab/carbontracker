from unittest import TestCase, mock
from carbontracker.emissions.intensity.fetcher import IntensityFetcher


class TestIntensityFetcher(TestCase):
    def test_suitable_not_implemented(self):
        fetcher = IntensityFetcher(logger = mock.Mock())

        with self.assertRaises(NotImplementedError):
            fetcher.suitable(mock.MagicMock())

    def test_carbon_intensity_not_implemented(self):
        fetcher = IntensityFetcher(logger = mock.Mock())

        with self.assertRaises(NotImplementedError):
            fetcher.fetch_carbon_intensity(mock.MagicMock())
