from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cli_analyze_emotion_command() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    memory_path = repo_root / "tests" / "tmp_cli_memory.json"
    profile_path = repo_root / "tests" / "tmp_cli_profiles.json"
    expression_path = repo_root / "tests" / "tmp_cli_expressions.json"
    if memory_path.exists():
        memory_path.unlink()
    if profile_path.exists():
        profile_path.unlink()
    if expression_path.exists():
        expression_path.unlink()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--memory-path",
            str(memory_path),
            "--profile-path",
            str(profile_path),
            "--expression-path",
            str(expression_path),
            "analyze-emotion",
            "sleepy-cat.jpg",
            "--pet-id",
            "pet-2",
            "--pet-name",
            "Luna",
            "--species",
            "cat",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Emotion: relaxed" in result.stdout
    assert "Observed Species: cat" in result.stdout
    assert "Confidence: 0.88" in result.stdout
    assert profile_path.exists()


def test_cli_reuses_cached_analysis_across_task_views() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    memory_path = repo_root / "tests" / "tmp_cli_persisted_memory.json"
    profile_path = repo_root / "tests" / "tmp_cli_persisted_profiles.json"
    expression_path = repo_root / "tests" / "tmp_cli_persisted_expressions.json"
    if memory_path.exists():
        memory_path.unlink()
    if profile_path.exists():
        profile_path.unlink()
    if expression_path.exists():
        expression_path.unlink()

    analyze = [
        sys.executable,
        "-m",
        "cli.main",
        "--memory-path",
        str(memory_path),
        "--profile-path",
        str(profile_path),
        "--expression-path",
        str(expression_path),
        "analyze-emotion",
        "happy-dog.jpg",
        "--pet-id",
        "pet-persisted",
        "--pet-name",
        "Milo",
        "--species",
        "dog",
    ]
    subprocess.run(analyze, cwd=repo_root, capture_output=True, text=True, check=True)

    motivation = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--memory-path",
            str(memory_path),
            "--profile-path",
            str(profile_path),
            "--expression-path",
            str(expression_path),
            "analyze-motivation",
            "happy-dog.jpg",
            "--pet-id",
            "pet-persisted",
            "--pet-name",
            "Milo",
            "--species",
            "dog",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    expression = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--memory-path",
            str(memory_path),
            "--profile-path",
            str(profile_path),
            "--expression-path",
            str(expression_path),
            "express-pet",
            "happy-dog.jpg",
            "--pet-id",
            "pet-persisted",
            "--pet-name",
            "Milo",
            "--species",
            "dog",
            "--locale",
            "zh-CN",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Motivation: seeking engagement" in motivation.stdout
    assert "Locale: zh-CN" in expression.stdout
    assert "Pet Voice: 我想和你互动一下" in expression.stdout
def test_cli_analyze_emotion_supports_video_modality() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    memory_path = repo_root / "tests" / "tmp_cli_video_memory.json"
    profile_path = repo_root / "tests" / "tmp_cli_video_profiles.json"
    expression_path = repo_root / "tests" / "tmp_cli_video_expressions.json"
    for path in (memory_path, profile_path, expression_path):
        if path.exists():
            path.unlink()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--memory-path",
            str(memory_path),
            "--profile-path",
            str(profile_path),
            "--expression-path",
            str(expression_path),
            "analyze-emotion",
            "zoom-play.mp4",
            "--pet-id",
            "pet-video",
            "--pet-name",
            "Milo",
            "--species",
            "dog",
            "--modality",
            "video",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Emotion: excited" in result.stdout


def test_cli_reports_species_mismatch_warning() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    memory_path = repo_root / "tests" / "tmp_cli_species_memory.json"
    profile_path = repo_root / "tests" / "tmp_cli_species_profiles.json"
    expression_path = repo_root / "tests" / "tmp_cli_species_expressions.json"
    for path in (memory_path, profile_path, expression_path):
        if path.exists():
            path.unlink()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--memory-path",
            str(memory_path),
            "--profile-path",
            str(profile_path),
            "--expression-path",
            str(expression_path),
            "analyze-emotion",
            "sleepy-cat.jpg",
            "--pet-id",
            "pet-species",
            "--pet-name",
            "Luna",
            "--species",
            "dog",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Observed Species: cat" in result.stdout
    assert "Species Warning:" in result.stdout


def test_cli_identity_enroll_and_verify() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    identity_path = repo_root / "tests" / "tmp_cli_identity_profiles.json"
    if identity_path.exists():
        identity_path.unlink()

    enroll = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "enroll-identity",
            str(repo_root / "tests" / "coconut.jpg"),
            "--pet-id",
            "pet-identity-cli",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    verify = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "verify-identity",
            str(repo_root / "tests" / "coconut.jpg"),
            "--pet-id",
            "pet-identity-cli",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "References: 1" in enroll.stdout
    assert "Enrollment Mode: append" in enroll.stdout
    assert "Match: yes" in verify.stdout


def test_cli_identity_verify_handles_missing_profile() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    identity_path = repo_root / "tests" / "tmp_cli_identity_missing.json"
    if identity_path.exists():
        identity_path.unlink()

    verify = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "verify-identity",
            str(repo_root / "tests" / "coconut.jpg"),
            "--pet-id",
            "missing-pet",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Match: no" in verify.stdout
    assert "Compared References: 0" in verify.stdout


def test_cli_identity_enroll_appends_reference_views() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    identity_path = repo_root / "tests" / "tmp_cli_identity_profiles.json"
    if identity_path.exists():
        identity_path.unlink()

    first_enroll = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "enroll-identity",
            str(repo_root / "tests" / "coconut.jpg"),
            "--pet-id",
            "pet-identity-cli",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    second_enroll = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "enroll-identity",
            str(repo_root / "tests" / "tuna.jpg"),
            "--pet-id",
            "pet-identity-cli",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    verify = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "--identity-path",
            str(identity_path),
            "verify-identity",
            str(repo_root / "tests" / "coconut.jpg"),
            "--pet-id",
            "pet-identity-cli",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "References: 1" in first_enroll.stdout
    assert "References: 2" in second_enroll.stdout
    assert "Compared References: 2" in verify.stdout
