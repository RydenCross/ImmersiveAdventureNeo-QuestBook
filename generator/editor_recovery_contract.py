from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from generator.editor_model import EditorOperation, apply_editor_operation
from generator.editor_recovery import EditorRecoveryStore
from generator.editor_service import EditorSession, handle_editor_api
from generator.editor_ui import EDITOR_HTML
from generator.modpack_content_scanner_contract import _synthetic_pack


@dataclass(frozen=True, slots=True)
class EditorRecoveryContract:
    autosave_after_edit: bool
    snapshot_round_trip: bool
    bounded_snapshots: bool
    corrupt_recovery_rejected: bool
    save_clears_autosave: bool
    recovery_api_routes: bool
    visual_recovery_controls: bool

    @property
    def is_clean(self) -> bool:
        return all(
            (
                self.autosave_after_edit,
                self.snapshot_round_trip,
                self.bounded_snapshots,
                self.corrupt_recovery_rejected,
                self.save_clears_autosave,
                self.recovery_api_routes,
                self.visual_recovery_controls,
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.is_clean else "fail",
            "autosave_after_edit": self.autosave_after_edit,
            "snapshot_round_trip": self.snapshot_round_trip,
            "bounded_snapshots": self.bounded_snapshots,
            "corrupt_recovery_rejected": self.corrupt_recovery_rejected,
            "save_clears_autosave": self.save_clears_autosave,
            "recovery_api_routes": self.recovery_api_routes,
            "visual_recovery_controls": self.visual_recovery_controls,
        }

    def format_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def format(self) -> str:
        return "\n".join(
            (
                f"Editor recovery contract: {'PASS' if self.is_clean else 'FAIL'}",
                f"Autosave after edit: {'PASS' if self.autosave_after_edit else 'FAIL'}.",
                f"Snapshot round trip: {'PASS' if self.snapshot_round_trip else 'FAIL'}.",
                f"Bounded snapshots: {'PASS' if self.bounded_snapshots else 'FAIL'}.",
                "Corrupt recovery rejected: "
                f"{'PASS' if self.corrupt_recovery_rejected else 'FAIL'}.",
                f"Save clears autosave: {'PASS' if self.save_clears_autosave else 'FAIL'}.",
                f"Recovery API routes: {'PASS' if self.recovery_api_routes else 'FAIL'}.",
                "Visual recovery controls: "
                f"{'PASS' if self.visual_recovery_controls else 'FAIL'}.",
            )
        )


def run_editor_recovery_contract() -> EditorRecoveryContract:
    with TemporaryDirectory(prefix="editor-recovery-contract-") as temporary:
        root = Path(temporary)
        pack = root / "recovery.mrpack"
        _synthetic_pack(pack)
        session = EditorSession.from_source(
            pack,
            workspace=root / "workspace",
            target_quests=4,
            chapter_size=10,
            reward_policy="conservative",
        )
        quest = session.document.quests[0]
        session.apply(
            {
                "action": "update_quest",
                "target_id": quest.quest_id,
                "values": {"title": "Checkpoint title"},
            }
        )
        recovery_status = session.recovery_payload()
        autosave_after_edit = bool(
            recovery_status["autosave_available"]
            and recovery_status["autosave"]["revision"] == session.document.revision
        )

        checkpoint = session.create_snapshot({"reason": "contract checkpoint"})
        snapshot_name = Path(str(checkpoint["snapshot"]["path"])).name
        session.apply(
            {
                "action": "update_quest",
                "target_id": quest.quest_id,
                "values": {"title": "Later title"},
            }
        )
        restored = session.recover({"snapshot": snapshot_name})
        snapshot_round_trip = bool(
            restored["status"] == "pass"
            and session.document.quests[0].title == "Checkpoint title"
            and session.status()["undo_depth"] == 0
        )

        bounded_store = EditorRecoveryStore(root / "bounded", max_snapshots=3)
        current = session.document
        for index in range(5):
            transaction = apply_editor_operation(
                current,
                EditorOperation.create(
                    "update_quest",
                    current.quests[0].quest_id,
                    title=f"Snapshot {index}",
                ),
            )
            if transaction.is_clean:
                current = transaction.after
                bounded_store.create_snapshot(current, reason=f"snapshot-{index}")
        bounded_snapshots = len(bounded_store.list_snapshots()) == 3

        session.apply(
            {
                "action": "update_quest",
                "target_id": quest.quest_id,
                "values": {"title": "Corrupt me"},
            }
        )
        session.recovery.autosave_path.write_text("{broken", encoding="utf-8")
        corrupt_response = handle_editor_api(session, "POST", "/api/v1/recover", {})
        corrupt_recovery_rejected = (
            corrupt_response.status_code == 400
            and corrupt_response.payload.get("status") == "fail"
        )

        session.recovery.autosave(session.document, reason="repair")
        save_result = session.save("models/recovered.json")
        save_clears_autosave = bool(
            save_result["status"] == "pass"
            and not session.recovery.autosave_path.exists()
        )

        session.apply(
            {
                "action": "update_quest",
                "target_id": quest.quest_id,
                "values": {"title": "API autosave"},
            }
        )
        api_status = handle_editor_api(session, "GET", "/api/v1/recovery")
        api_snapshot = handle_editor_api(
            session,
            "POST",
            "/api/v1/snapshot",
            {"reason": "api checkpoint"},
        )
        api_recover = handle_editor_api(session, "POST", "/api/v1/recover", {})
        api_discard = handle_editor_api(
            session,
            "POST",
            "/api/v1/discard-recovery",
            {"keep_snapshots": True},
        )
        recovery_api_routes = all(
            response.status_code == 200
            for response in (api_status, api_snapshot, api_recover, api_discard)
        )

        visual_recovery_controls = all(
            token in EDITOR_HTML
            for token in (
                'id="snapshot-button"',
                'id="recover-button"',
                "/snapshot",
                "/recover",
                "autosave_available",
            )
        )

        return EditorRecoveryContract(
            autosave_after_edit=autosave_after_edit,
            snapshot_round_trip=snapshot_round_trip,
            bounded_snapshots=bounded_snapshots,
            corrupt_recovery_rejected=corrupt_recovery_rejected,
            save_clears_autosave=save_clears_autosave,
            recovery_api_routes=recovery_api_routes,
            visual_recovery_controls=visual_recovery_controls,
        )
