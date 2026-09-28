from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

from scripts import sage_assets


class SageAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        (self.root / "properties/sage/textures").mkdir(parents=True)
        (self.root / ".local").mkdir()
        (self.root / "properties/sage/sage.blend").write_bytes(b"blend-v1")
        (self.root / "properties/sage/textures/wall.png").write_bytes(b"texture-v1")
        (self.root / ".local/sage-furniture-unbatched.glb").write_bytes(b"furniture-v1")
        self.provenance = mock.patch.object(
            sage_assets,
            "_source_provenance",
            return_value={"revision": "a" * 40, "worktree_dirty": True},
        )
        self.provenance.start()
        self.addCleanup(self.provenance.stop)

    def pack(self, name="candidate"):
        return sage_assets.pack(self.root, Path(self.temporary.name) / name)

    def test_pack_recover_integrity_and_overwrite_protection(self):
        archive, _, candidate = self.pack()
        destination = Path(self.temporary.name) / "recovered"
        bundle = candidate["candidate"]

        sage_assets.recover(archive, bundle, destination)
        for payload in bundle["payloads"]:
            source = self.root / payload["path"]
            recovered = destination / payload["path"]
            self.assertEqual(source.read_bytes(), recovered.read_bytes())

        master = destination / sage_assets.MASTER
        master.write_bytes(b"authored-change")
        with self.assertRaisesRegex(sage_assets.AssetError, "Refusing to overwrite"):
            sage_assets.recover(archive, bundle, destination)
        self.assertEqual(master.read_bytes(), b"authored-change")

        sage_assets.recover(archive, bundle, destination, force=True)
        self.assertEqual(master.read_bytes(), b"blend-v1")

    def test_recover_rejects_traversal_links_and_destination_symlinks(self):
        archive, _, candidate = self.pack()
        bundle = candidate["candidate"]
        malicious = Path(self.temporary.name) / "traversal.zip"
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(malicious, "w") as target:
            for info in source.infolist():
                target.writestr(info, source.read(info))
            target.writestr("../escape", b"escape")
        with self.assertRaisesRegex(sage_assets.AssetError, "Unsafe archive path"):
            sage_assets.validate_archive(malicious)

        linked = Path(self.temporary.name) / "link.zip"
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(linked, "w") as target:
            for info in source.infolist():
                if info.filename == sage_assets.MASTER:
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                target.writestr(info, source.read(info))
        with self.assertRaisesRegex(sage_assets.AssetError, "directory or link"):
            sage_assets.validate_archive(linked)

        destination = Path(self.temporary.name) / "linked-destination"
        destination.mkdir()
        (destination / "properties").symlink_to(self.root / "properties", target_is_directory=True)
        with self.assertRaisesRegex(sage_assets.AssetError, "traverses a symlink"):
            sage_assets.recover(archive, bundle, destination)

    def test_publish_verifies_before_manifest_and_retains_current_plus_previous(self):
        fake_bin, fake_state = self.make_fake_gh()
        manifest = Path(self.temporary.name) / "published.json"
        manifest.write_text(json.dumps({
            "format_version": 1,
            "repository": sage_assets.REPOSITORY,
            "release": {"tag": sage_assets.RELEASE_TAG, "prerelease": True},
            "current": None,
            "previous": None,
        }))
        environment = {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_STATE": str(fake_state),
        }
        with mock.patch.dict(os.environ, environment):
            bundles = []
            for version in range(1, 3):
                (self.root / "properties/sage/sage.blend").write_bytes(f"blend-v{version}".encode())
                _, candidate_path, candidate = self.pack(f"candidate-{version}")
                bundles.append(candidate["candidate"])
                sage_assets.publish(candidate_path, manifest)

            before_cleanup_failure = manifest.read_bytes()
            (self.root / "properties/sage/sage.blend").write_bytes(b"blend-v3")
            _, candidate_path, candidate = self.pack("candidate-3")
            bundles.append(candidate["candidate"])
            with mock.patch.object(sage_assets, "_prune", side_effect=sage_assets.AssetError("transient cleanup failure")):
                with self.assertRaisesRegex(sage_assets.AssetError, "transient cleanup failure"):
                    sage_assets.publish(candidate_path, manifest)
            self.assertEqual(manifest.read_bytes(), before_cleanup_failure)
            sage_assets.publish(candidate_path, manifest)

            published = json.loads(manifest.read_text())
            self.assertEqual(published["current"]["archive_name"], bundles[2]["archive_name"])
            self.assertEqual(published["previous"]["archive_name"], bundles[1]["archive_name"])
            self.assertEqual(
                sorted(path.name for path in (fake_state / "assets").iterdir()),
                sorted([bundles[1]["archive_name"], bundles[2]["archive_name"]]),
            )
            events = (fake_state / "events").read_text().splitlines()
            upload = events.index(f"upload:{bundles[2]['archive_name']}")
            download = events.index(f"download:{bundles[2]['archive_name']}")
            deletion = events.index(f"delete:{bundles[0]['archive_name']}")
            self.assertLess(upload, download)
            self.assertLess(download, deletion)

            event_count = len(events)
            sage_assets.publish(candidate_path, manifest)
            repeated_events = (fake_state / "events").read_text().splitlines()[event_count:]
            self.assertIn(f"download:{bundles[2]['archive_name']}", repeated_events)
            self.assertFalse(any(event.startswith(("upload:", "delete:")) for event in repeated_events))

            before_failure = manifest.read_bytes()
            (self.root / "properties/sage/sage.blend").write_bytes(b"blend-v4")
            _, failed_candidate, failed = self.pack("candidate-4")
            with mock.patch.dict(os.environ, {"FAKE_GH_CORRUPT_DOWNLOAD": "1"}):
                with self.assertRaisesRegex(sage_assets.AssetError, "SHA-256"):
                    sage_assets.publish(failed_candidate, manifest)
            self.assertEqual(manifest.read_bytes(), before_failure)
            events = (fake_state / "events").read_text().splitlines()
            failed_upload = events.index(f"upload:{failed['candidate']['archive_name']}")
            self.assertFalse(any(event.startswith("delete:") for event in events[failed_upload:]))

    def test_publish_from_stale_manifest_cannot_prune_newer_bundle(self):
        fake_bin, fake_state = self.make_fake_gh()
        manifest = Path(self.temporary.name) / "published.json"
        manifest.write_text(json.dumps({
            "format_version": 1,
            "repository": sage_assets.REPOSITORY,
            "release": {"tag": sage_assets.RELEASE_TAG, "prerelease": True},
            "current": None,
            "previous": None,
        }))
        environment = {
            "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_STATE": str(fake_state),
        }
        with mock.patch.dict(os.environ, environment):
            _, candidate_a, bundle_a = self.pack("candidate-a")
            sage_assets.publish(candidate_a, manifest)
            stale_manifest = manifest.read_bytes()
            (self.root / "properties/sage/sage.blend").write_bytes(b"blend-b")
            _, candidate_b, bundle_b = self.pack("candidate-b")
            sage_assets.publish(candidate_b, manifest)

            manifest.write_bytes(stale_manifest)
            (self.root / "properties/sage/sage.blend").write_bytes(b"blend-c")
            _, candidate_c, _ = self.pack("candidate-c")
            with self.assertRaisesRegex(sage_assets.AssetError, "not represented"):
                sage_assets.publish(candidate_c, manifest)
            with self.assertRaisesRegex(sage_assets.AssetError, "not represented"):
                sage_assets.publish(candidate_a, manifest)

        self.assertEqual(
            sorted(path.name for path in (fake_state / "assets").iterdir()),
            sorted([
                bundle_a["candidate"]["archive_name"],
                bundle_b["candidate"]["archive_name"],
            ]),
        )

    def make_fake_gh(self):
        fake_bin = Path(self.temporary.name) / "bin"
        fake_state = Path(self.temporary.name) / "gh-state"
        fake_bin.mkdir()
        fake_state.mkdir()
        script = fake_bin / "gh"
        script.write_text("""#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import sys

args = sys.argv[1:]
state = Path(os.environ["FAKE_GH_STATE"])
assets = state / "assets"
assets.mkdir(exist_ok=True)
with (state / "events").open("a") as events:
    if args[:2] == ["release", "view"]:
        events.write("view\\n")
        if not (state / "release").exists():
            print("release not found", file=sys.stderr)
            sys.exit(1)
        print(json.dumps({
            "tagName": "sage-assets",
            "isPrerelease": True,
            "isImmutable": False,
            "assets": [{"name": path.name} for path in sorted(assets.iterdir())],
        }))
    elif args[:2] == ["release", "create"]:
        events.write("create\\n")
        (state / "release").write_text("created")
    elif args[:2] == ["release", "upload"]:
        source = Path(args[3])
        events.write(f"upload:{source.name}\\n")
        shutil.copyfile(source, assets / source.name)
    elif args[:2] == ["release", "download"]:
        name = args[args.index("--pattern") + 1]
        destination = Path(args[args.index("--dir") + 1]) / name
        events.write(f"download:{name}\\n")
        shutil.copyfile(assets / name, destination)
        if os.environ.get("FAKE_GH_CORRUPT_DOWNLOAD"):
            destination.write_bytes(b"corrupt")
    elif args[:2] == ["release", "delete-asset"]:
        name = args[3]
        events.write(f"delete:{name}\\n")
        (assets / name).unlink()
    else:
        print(f"unsupported fake gh invocation: {args}", file=sys.stderr)
        sys.exit(2)
""")
        script.chmod(0o755)
        return fake_bin, fake_state


if __name__ == "__main__":
    unittest.main()
