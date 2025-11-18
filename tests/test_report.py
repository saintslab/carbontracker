import io
import os
import sys
import tempfile
import types
import unittest
from unittest import mock


def _install_reportlab_stubs():
    """Provides minimal reportlab replacements so report.py can be imported."""
    reportlab_module = types.ModuleType("reportlab")
    lib_module = types.ModuleType("reportlab.lib")
    reportlab_module.lib = lib_module

    colors_module = types.ModuleType("reportlab.lib.colors")
    colors_module.HexColor = lambda value: value
    lib_module.colors = colors_module

    pagesizes_module = types.ModuleType("reportlab.lib.pagesizes")
    pagesizes_module.letter = ("letter", "letter")
    lib_module.pagesizes = pagesizes_module

    units_module = types.ModuleType("reportlab.lib.units")
    units_module.inch = 1
    lib_module.units = units_module

    styles_module = types.ModuleType("reportlab.lib.styles")

    def getSampleStyleSheet():
        return {"Heading1": object(), "Heading2": object(), "Normal": object()}

    class ParagraphStyle:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    styles_module.getSampleStyleSheet = getSampleStyleSheet
    styles_module.ParagraphStyle = ParagraphStyle
    lib_module.styles = styles_module

    platypus_module = types.ModuleType("reportlab.platypus")

    class SimpleDocTemplate:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def build(self, story):
            self.story = story

    class Paragraph:
        def __init__(self, text, style):
            self.text = text
            self.style = style

    class Spacer:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    class Table:
        def __init__(self, data, colWidths=None, rowHeights=None):
            self.data = data
            self.colWidths = colWidths
            self.rowHeights = rowHeights

        def setStyle(self, style):
            self.style = style

    class TableStyle:
        def __init__(self, instructions):
            self.instructions = instructions

    class Image:
        def __init__(self, data, width=None, height=None):
            self.data = data
            self.width = width
            self.height = height

    platypus_module.SimpleDocTemplate = SimpleDocTemplate
    platypus_module.Paragraph = Paragraph
    platypus_module.Spacer = Spacer
    platypus_module.Table = Table
    platypus_module.TableStyle = TableStyle
    platypus_module.Image = Image
    reportlab_module.platypus = platypus_module

    module_map = {
        "reportlab": reportlab_module,
        "reportlab.lib": lib_module,
        "reportlab.lib.colors": colors_module,
        "reportlab.lib.pagesizes": pagesizes_module,
        "reportlab.lib.styles": styles_module,
        "reportlab.lib.units": units_module,
        "reportlab.platypus": platypus_module,
    }

    for name, module in module_map.items():
        sys.modules.setdefault(name, module)


try:
    from carbontracker import report
except ModuleNotFoundError as exc:
    if exc.name and exc.name.startswith("reportlab"):
        _install_reportlab_stubs()
        from carbontracker import report
    else:
        raise


SAMPLE_LOG = """\
2025-11-18 15:53:54 - carbontracker version 2.3.4.dev1+g61759d185.d20251107
2025-11-18 15:53:54 - Only predicted and actual consumptions are multiplied by a PUE coefficient of 1.58 (Daniel Bizo, 2023, Uptime Institute Global Data Center Survey).
2025-11-18 15:53:54 - The following components were found: GPU with device(s) GPU, ANE. CPU with device(s) CPU.
2025-11-18 15:53:54 - Monitoring thread started.
2025-11-18 15:54:28 - Epoch 1:
2025-11-18 15:54:28 - Duration: 0:00:33.57
2025-11-18 15:54:28 - Average power usage (W) for gpu: 0.019533333333333337
2025-11-18 15:54:28 - Average power usage (W) for cpu: 6.785066666666666
2025-11-18 15:54:28 - Carbon intensities (gCO2eq/kWh) fetched every 900 s at detected location: Copenhagen, Capital Region, DK: [143.3]
2025-11-18 15:54:28 - Average carbon intensity during training was 143.30 gCO2eq/kWh. 
2025-11-18 15:54:28 - Monitoring thread ended.
"""


class TestReportModule(unittest.TestCase):
    def setUp(self):
        self.parser = report.LogParser(SAMPLE_LOG)

    def test_format_duration_produces_readable_value(self):
        self.assertEqual(report.format_duration(3661), "1h 1min 1s")
        self.assertEqual(report.format_duration(59), "59s")

    def test_log_parser_extracts_metadata_and_epochs(self):
        parser = self.parser
        self.assertEqual(parser.version, "2.3.4.")
        self.assertEqual(parser.pue, 1.58)
        self.assertIsNone(parser.location)
        self.assertEqual(parser.start_time, "2025-11-18 15:53:54")
        self.assertEqual(parser.end_time, "2025-11-18 15:54:28")
        self.assertEqual(len(parser.epochs), 1)
        self.assertAlmostEqual(parser.epochs[0]["duration"], 33.57)
        self.assertAlmostEqual(parser.epochs[0]["gpu_power"], 0.019533333333333337)
        self.assertAlmostEqual(parser.epochs[0]["cpu_power"], 6.785066666666666)
        self.assertAlmostEqual(parser.epochs[0]["total_power"], 6.8046)

    def test_calculate_energy_metrics_matches_expected_numbers(self):
        metrics = self.parser.calculate_energy_metrics()
        self.assertAlmostEqual(metrics["total_duration"], 33.57)
        self.assertAlmostEqual(metrics["avg_gpu_power"], 0.019533333333333337)
        self.assertAlmostEqual(metrics["avg_cpu_power"], 6.785066666666666)
        self.assertAlmostEqual(metrics["total_power"], 6.8046)
        self.assertAlmostEqual(metrics["energy_kwh"], 6.345289499999999e-05, places=12)
        self.assertAlmostEqual(metrics["co2_kg"], 9.092799853499999e-06, places=12)

    def test_generate_plots_returns_png_buffer(self):
        plots = self.parser.generate_plots()
        self.assertIn("combined_plots", plots)
        plot_buffer = plots["combined_plots"]
        self.assertGreater(len(plot_buffer.getvalue()), 0)

    def test_generate_report_from_log_builds_document(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = os.path.join(tmp_dir, "training.log")
            output_path = os.path.join(tmp_dir, "report.pdf")
            with open(log_path, "w", encoding="utf-8") as log_file:
                log_file.write(SAMPLE_LOG)

            with mock.patch("carbontracker.report.SimpleDocTemplate") as mock_doc_template, mock.patch(
                "carbontracker.report.Image"
            ) as mock_image:
                mock_image.return_value = mock.Mock(name="ImageFlowable")
                doc_instance = mock_doc_template.return_value
                report.generate_report_from_log(log_path, output_path)

            mock_doc_template.assert_called_once_with(
                output_path, pagesize=report.letter, rightMargin=72, leftMargin=72, topMargin=24, bottomMargin=72
            )
            doc_instance.build.assert_called_once()
            story_passed = doc_instance.build.call_args[0][0]
            self.assertGreater(len(story_passed), 0)
            self.assertTrue(any(isinstance(flowable, report.Paragraph) for flowable in story_passed))

