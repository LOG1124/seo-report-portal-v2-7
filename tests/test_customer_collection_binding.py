"""Customer isolation and first-party collection preflight without live APIs."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "scripts"))

import google_api_collector as collector  # noqa: E402


class CustomerCollectionBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = self.root / "source"
        self.archive.mkdir()
        self.customers = self.root / "private" / "customers"
        (self.archive / "customer-registry.json").write_text(json.dumps({"customers": [
            {"canonical_domain": domain, "portal_slug": domain.replace(".", "-"), "status": "active"}
            for domain in ("alpha.com", "beta.com")
        ]}), encoding="utf-8")
        for domain, property_id in (("alpha.com", "111"), ("beta.com", "222")):
            self.write_customer(domain, domain, property_id)

    def write_customer(self, folder_domain, project_domain, property_id, *, gsc_domain=None):
        folder = self.customers / folder_domain
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "project-input.json").write_text(json.dumps({
            "website_url": f"https://{project_domain}", "report_start": "2026-07-01",
            "report_end": "2026-07-31", "cooperation_level": "standard",
        }), encoding="utf-8")
        (folder / "google-api.json").write_text(json.dumps({
            "credentials_file": "private/google-service-account.json",
            "service_account_email": "service@example.invalid",
            "ga4": {"property_id": property_id},
            "gsc": {"site_url": f"sc-domain:{gsc_domain or folder_domain}"},
        }), encoding="utf-8")

    def command(self, *, month="2026-07"):
        return ["google_api_collector.py", "--domain", "alpha.com", "--customer-root", str(self.customers),
                "--archive-root", str(self.archive), "--month", month, "--archive-only"]

    def test_other_customer_project_or_gsc_stops_before_credentials_and_api(self):
        for project_domain, gsc_domain in (("beta.com", "alpha.com"), ("alpha.com", "beta.com")):
            with self.subTest(project_domain=project_domain, gsc_domain=gsc_domain):
                self.write_customer("alpha.com", project_domain, "111", gsc_domain=gsc_domain)
                with patch.object(sys, "argv", self.command()), patch.object(
                    collector, "_credential_path", side_effect=AssertionError("credentials accessed too early")
                ), self.assertRaisesRegex(ValueError, "域名.*不匹配"):
                    collector.main()

    def test_shared_access_denied_stops_before_config_and_api(self):
        with patch.object(sys, "argv", self.command()), patch.object(
            collector.os, "scandir", side_effect=PermissionError("denied")
        ), patch.object(collector, "_load_object", side_effect=AssertionError("config accessed too early")), self.assertRaisesRegex(
            PermissionError, "共享源档拒绝访问"
        ):
            collector.main()

    def test_ready_archive_is_reused_without_api_or_overwrite(self):
        collector.save_new_month_archive(self.archive, "alpha.com", "2026-07", {
            "domain": "alpha.com", "period": ["2026-07-01", "2026-07-31"],
            "ga4": {"session_count": 1}, "gsc": {"organic_clicks": 1},
        })
        with patch.object(sys, "argv", self.command()), patch.object(
            collector, "_credential_path", side_effect=AssertionError("credentials accessed too early")
        ), self.assertRaisesRegex(FileExistsError, "完整原始档案已存在"):
            collector.main()

    def test_partial_archive_and_other_customer_local_output_stop_before_api(self):
        path = self.archive / "ga4-gsc" / "alpha.com" / "2026-07.json"
        path.parent.mkdir(parents=True)
        path.write_text("{}", encoding="utf-8")
        with patch.object(sys, "argv", self.command()), patch.object(
            collector, "_credential_path", side_effect=AssertionError("credentials accessed too early")
        ), self.assertRaisesRegex(ValueError, "缺少 ready 标记"):
            collector.main()
        path.unlink()
        args = self.command()[:-1] + ["--collected-data", str(self.customers / "beta.com" / "collected_data.json")]
        with patch.object(sys, "argv", args), patch.object(
            collector, "_credential_path", side_effect=AssertionError("credentials accessed too early")
        ), self.assertRaisesRegex(ValueError, "只能写入当前客户文件"):
            collector.main()

    def test_custom_comparison_uses_only_requested_customer(self):
        self.write_customer("alpha.com", "beta.com", "111")
        with patch.object(collector, "_credential_path", side_effect=AssertionError("credentials accessed too early")), self.assertRaisesRegex(
            ValueError, "客户配置域名不匹配"
        ):
            collector.collect_custom_archive_from_project(
                self.archive, self.customers, "alpha.com", "2026-06-01", "2026-06-15"
            )

    def test_single_platform_dry_run_can_diagnose_ga4_without_gsc_binding(self):
        self.write_customer("alpha.com", "alpha.com", "111", gsc_domain="beta.com")
        args = self.command()[:-1] + ["--platform", "ga4", "--dry-run"]
        with patch.object(sys, "argv", args), patch.object(
            collector, "_credential_path", return_value=Path("credential.json")
        ), patch.object(collector, "_validate_credential_identity"), patch.object(
            collector, "build_clients", return_value=(object(), None)
        ), patch.object(collector, "collect_ga4", return_value={"session_count": 1}) as ga4, patch.object(
            collector, "collect_gsc", side_effect=AssertionError("GSC must not run")
        ), patch.object(collector, "save_new_month_archive", side_effect=AssertionError("dry-run must not archive")):
            self.assertEqual(collector.main(), 0)
        self.assertEqual(ga4.call_args.args[1], "111")

    def test_missing_archive_reaches_only_current_customer_google_api(self):
        with patch.object(sys, "argv", self.command()), patch.object(
            collector, "_credential_path", return_value=Path("credential.json")
        ), patch.object(collector, "_validate_credential_identity"), patch.object(
            collector, "build_clients", return_value=(object(), object())
        ), patch.object(collector, "collect_ga4", return_value={"session_count": 1}) as ga4, patch.object(
            collector, "collect_gsc", return_value={"organic_clicks": 1, "ranked_keyword_count": 1}
        ) as gsc, patch.object(collector, "save_new_month_archive") as save:
            self.assertEqual(collector.main(), 0)
        self.assertEqual(ga4.call_args.args[1], "111")
        self.assertEqual(gsc.call_args.args[1], "sc-domain:alpha.com")
        self.assertEqual(save.call_args.args[1], "alpha.com")


if __name__ == "__main__":
    unittest.main()
