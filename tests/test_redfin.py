"""Comprehensive tests for the redfin library."""
import json
import time
import unittest
from unittest.mock import MagicMock, patch, call

from redfin import Redfin
from redfin.redfin import DEFAULT_USER_AGENT


def make_response(payload, result_code=0, error_message="Success", status_code=200):
    """Create a mock requests.Response with proper redfin API shape."""
    data = {
        "errorMessage": error_message,
        "resultCode": result_code,
        "payload": payload,
    }
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = "{}&&" + json.dumps(data)
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


class TestUserAgent(unittest.TestCase):
    """Test that User-Agent header is set correctly."""

    @patch("redfin.redfin.requests.get")
    def test_default_user_agent(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.meta_request("api/home/details/initialInfo", {"path": "/some/path"})
        sent_headers = mock_get.call_args[1]["headers"]
        self.assertEqual(sent_headers["user-agent"], DEFAULT_USER_AGENT)

    @patch("redfin.redfin.requests.get")
    def test_custom_user_agent(self, mock_get):
        mock_get.return_value = make_response({})
        custom_ua = "MyBot/1.0"
        client = Redfin(user_agent=custom_ua)
        client.meta_request("api/home/details/initialInfo", {"path": "/some/path"})
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs["headers"]["user-agent"], custom_ua)

    def test_default_user_agent_value(self):
        client = Redfin()
        self.assertIn("Mozilla/5.0", client.user_agent_header["user-agent"])
        self.assertIn("Chrome/120.0.0.0", client.user_agent_header["user-agent"])

    def test_user_agent_override(self):
        client = Redfin(user_agent="TestAgent/2.0")
        self.assertEqual(client.user_agent_header["user-agent"], "TestAgent/2.0")


class TestAccessLevel(unittest.TestCase):
    """Test that accessLevel=3 is sent in meta_property requests."""

    @patch("redfin.redfin.requests.get")
    def test_access_level_3_in_meta_property(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.meta_property("avm", {"propertyId": "12345", "listingId": ""})
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        self.assertEqual(params["accessLevel"], 3)

    @patch("redfin.redfin.requests.get")
    def test_avm_details_uses_access_level_3(self, mock_get):
        mock_get.return_value = make_response({"predictedValue": 500000})
        client = Redfin()
        client.avm_details("12345", "")
        call_kwargs = mock_get.call_args[1]
        params = call_kwargs["params"]
        self.assertEqual(params["accessLevel"], 3)


class TestAvmDetails(unittest.TestCase):
    """Test avm_details response parsing."""

    @patch("redfin.redfin.requests.get")
    def test_avm_details_strips_prefix(self, mock_get):
        """The API returns {}&&{...} — first 4 chars must be stripped."""
        payload = {
            "predictedValue": 750000,
            "sectionPreviewText": "Est. $750K",
            "latLong": {"latitude": 47.123, "longitude": -122.456},
            "streetAddress": {"assembledAddress": "1234 Main St"},
        }
        mock_get.return_value = make_response(payload)
        client = Redfin()
        result = client.avm_details("12345", "")
        self.assertEqual(result["resultCode"], 0)
        self.assertEqual(result["payload"]["predictedValue"], 750000)
        self.assertEqual(result["payload"]["sectionPreviewText"], "Est. $750K")

    @patch("redfin.redfin.requests.get")
    def test_avm_details_lat_long(self, mock_get):
        payload = {
            "latLong": {"latitude": 47.6062, "longitude": -122.3321},
        }
        mock_get.return_value = make_response(payload)
        client = Redfin()
        result = client.avm_details("99999", "")
        lat = result["payload"]["latLong"]["latitude"]
        lng = result["payload"]["latLong"]["longitude"]
        self.assertAlmostEqual(lat, 47.6062)
        self.assertAlmostEqual(lng, -122.3321)


class TestNeighborhoodStats(unittest.TestCase):
    """Test neighborhood_stats method."""

    @patch("redfin.redfin.requests.get")
    def test_neighborhood_stats_method_exists(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        self.assertTrue(hasattr(client, "neighborhood_stats"))
        self.assertTrue(callable(client.neighborhood_stats))

    @patch("redfin.redfin.requests.get")
    def test_neighborhood_stats_calls_correct_url(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.neighborhood_stats("12345")
        call_args = mock_get.call_args[0]
        url = call_args[0]
        self.assertIn("neighborhoodStats/statsInfo", url)

    @patch("redfin.redfin.requests.get")
    def test_neighborhood_stats_includes_property_id(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.neighborhood_stats("12345")
        params = mock_get.call_args[1]["params"]
        self.assertEqual(params["propertyId"], "12345")
        self.assertEqual(params["accessLevel"], 3)

    @patch("redfin.redfin.requests.get")
    def test_neighborhood_stats_returns_scores(self, mock_get):
        payload = {
            "addressInfo": {"city": "Seattle", "state": "WA"},
            "walkScoreInfo": {
                "walkScoreData": {
                    "walkScore": {"value": 92},
                    "bikeScore": {"value": 75},
                    "transitScore": {"value": 88},
                }
            },
        }
        mock_get.return_value = make_response(payload)
        client = Redfin()
        result = client.neighborhood_stats("12345")
        scores = result["payload"]["walkScoreInfo"]["walkScoreData"]
        self.assertEqual(scores["walkScore"]["value"], 92)
        self.assertEqual(scores["bikeScore"]["value"], 75)
        self.assertEqual(scores["transitScore"]["value"], 88)


class TestRateLimiting(unittest.TestCase):
    """Test 429 retry logic and request_delay."""

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_429_retry(self, mock_get, mock_sleep):
        """On 429 response, should sleep Retry-After seconds then retry once."""
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "30"}
        resp_429.raise_for_status = MagicMock()

        resp_ok = make_response({"predictedValue": 500000})

        mock_get.side_effect = [resp_429, resp_ok]

        client = Redfin()
        result = client.avm_details("12345", "")

        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(30)
        self.assertEqual(result["payload"]["predictedValue"], 500000)

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_429_default_retry_after(self, mock_get, mock_sleep):
        """If Retry-After header missing, should default to 60 seconds."""
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {}  # No Retry-After header
        resp_429.raise_for_status = MagicMock()

        resp_ok = make_response({})
        mock_get.side_effect = [resp_429, resp_ok]

        client = Redfin()
        client.search("test")

        mock_sleep.assert_called_once_with(60)

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_request_delay_calls_sleep(self, mock_get, mock_sleep):
        """request_delay should call time.sleep before each request."""
        mock_get.return_value = make_response({})
        client = Redfin(request_delay=2.5)
        client.search("123 Main St")
        mock_sleep.assert_called_once_with(2.5)

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_no_request_delay_by_default(self, mock_get, mock_sleep):
        """Default request_delay=0 should NOT call time.sleep."""
        mock_get.return_value = make_response({})
        client = Redfin()
        client.search("123 Main St")
        mock_sleep.assert_not_called()

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_request_delay_zero_no_sleep(self, mock_get, mock_sleep):
        """Explicit request_delay=0 should NOT call time.sleep."""
        mock_get.return_value = make_response({})
        client = Redfin(request_delay=0)
        client.avm_details("12345", "")
        mock_sleep.assert_not_called()


class TestExistingMethodsPreserved(unittest.TestCase):
    """Ensure above_the_fold and info_panel still exist."""

    def test_above_the_fold_exists(self):
        client = Redfin()
        self.assertTrue(hasattr(client, "above_the_fold"))

    def test_info_panel_exists(self):
        client = Redfin()
        self.assertTrue(hasattr(client, "info_panel"))

    @patch("redfin.redfin.requests.get")
    def test_above_the_fold_sends_request(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.above_the_fold("12345", "")
        self.assertTrue(mock_get.called)
        url = mock_get.call_args[0][0]
        self.assertIn("aboveTheFold", url)

    @patch("redfin.redfin.requests.get")
    def test_info_panel_sends_request(self, mock_get):
        mock_get.return_value = make_response({})
        client = Redfin()
        client.info_panel("12345", "")
        self.assertTrue(mock_get.called)
        url = mock_get.call_args[0][0]
        self.assertIn("mainHouseInfoPanelInfo", url)


class TestResponseFormat(unittest.TestCase):
    """Test response parsing edge cases."""

    @patch("redfin.redfin.requests.get")
    def test_empty_response_body_raises_value_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = ""
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        client = Redfin()
        with self.assertRaises(ValueError):
            client.search("test")

    @patch("redfin.redfin.requests.get")
    def test_html_response_raises_value_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<!DOCTYPE html><html><body>Captcha challenge</body></html>"
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        client = Redfin()
        with self.assertRaises(ValueError) as ctx:
            client.search("test")
        self.assertIn("Unexpected Redfin API response format", str(ctx.exception))

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_persistent_429_raises_http_error(self, mock_get, mock_sleep):
        import requests as req
        resp_429a = MagicMock()
        resp_429a.status_code = 429
        resp_429a.headers = {"Retry-After": "5"}
        resp_429a.raise_for_status = MagicMock()

        resp_429b = MagicMock()
        resp_429b.status_code = 429
        resp_429b.headers = {}
        resp_429b.raise_for_status.side_effect = req.exceptions.HTTPError("429 Too Many Requests")

        mock_get.side_effect = [resp_429a, resp_429b]
        client = Redfin()
        with self.assertRaises(req.exceptions.HTTPError):
            client.search("test")
        self.assertEqual(mock_get.call_count, 2)

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_retry_after_http_date_format_falls_back_to_60(self, mock_get, mock_sleep):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "Sat, 22 Mar 2026 00:00:00 GMT"}
        resp_429.raise_for_status = MagicMock()
        resp_ok = make_response({})
        mock_get.side_effect = [resp_429, resp_ok]
        client = Redfin()
        client.search("test")
        mock_sleep.assert_called_once_with(60)

    @patch("redfin.redfin.time.sleep")
    @patch("redfin.redfin.requests.get")
    def test_request_delay_applied_in_retry_path(self, mock_get, mock_sleep):
        from unittest.mock import call
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "10"}
        resp_429.raise_for_status = MagicMock()
        resp_ok = make_response({})
        mock_get.side_effect = [resp_429, resp_ok]
        client = Redfin(request_delay=1.5)
        client.search("test")
        # Should sleep: request_delay (before first), retry_after (on 429), request_delay (before retry)
        sleep_calls = mock_sleep.call_args_list
        self.assertIn(call(1.5), sleep_calls)
        self.assertIn(call(10), sleep_calls)


if __name__ == "__main__":
    unittest.main()
