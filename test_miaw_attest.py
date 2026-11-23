"""Direct-mode tests for MiawAttest.

Direct mode runs the contract in-process with gl.nondet.web and
gl.nondet.exec_prompt mocked, so these are milliseconds and need no keys,
no Docker and no network. What they cover: storage, argument validation,
the normalisation the contract does to an LLM answer, and — via
run_validator — whether a validator that reads the page differently agrees
or disagrees. What they deliberately do NOT cover: real validator consensus
on Bradbury with real LLMs.

Run from the project root:
  .venv/bin/pytest contracts/tests/direct -v
"""

import json
import pathlib

CONTRACT = str(pathlib.Path(__file__).resolve().parents[2] / "miaw_attest.py")

PAGE_SUPPORTS = (
    "GenLayer Season 2 points program is open. "
    "Anyone can join and earn points toward mainnet."
)
GOOD_ANSWER = json.dumps(
    {
        "verdict": "supported",
        "quote": "GenLayer Season 2 points program is open.",
        "source": "https://docs.genlayer.com/developers/networks",
    }
)
URLS = "https://docs.genlayer.com/developers/networks"
CLAIM = "GenLayer Season 2 points program is open"


def _mock_pages(direct_vm, body=PAGE_SUPPORTS):
    direct_vm.mock_web(r"https://.*", {"status": 200, "body": body})


def test_verdict_is_empty_before_any_attestation(direct_deploy):
    contract = direct_deploy(CONTRACT)
    result = contract.verdict(CLAIM)
    assert result["attested"] is False
    assert result["verdict"] == ""
    assert result["claim"] == CLAIM.lower()


def test_attest_stores_the_decision_fields(direct_vm, direct_deploy):
    _mock_pages(direct_vm)
    direct_vm.mock_llm(r".*", GOOD_ANSWER)
    contract = direct_deploy(CONTRACT)
    contract.attest(CLAIM, URLS)
    result = contract.verdict(CLAIM)
    assert result["attested"] is True
    assert result["verdict"] == "supported"
    assert result["quote"] == "GenLayer Season 2 points program is open."
    assert result["source"] == URLS
    assert contract.claims() == [CLAIM.lower()]


def test_claim_name_is_normalised(direct_vm, direct_deploy):
    _mock_pages(direct_vm)
    direct_vm.mock_llm(r".*", GOOD_ANSWER)
    contract = direct_deploy(CONTRACT)
    contract.attest("  GenLayer Season 2 Points Program Is Open  ", URLS)
    assert contract.verdict(CLAIM)["attested"] is True
    assert contract.verdict("GENLAYER SEASON 2 POINTS PROGRAM IS OPEN")["attested"] is True


def test_second_attestation_replaces_the_first_without_duplicating_the_key(
    direct_vm, direct_deploy
):
    _mock_pages(direct_vm)
    direct_vm.mock_llm(r".*", GOOD_ANSWER)
    contract = direct_deploy(CONTRACT)
    contract.attest(CLAIM, URLS)
    direct_vm.clear_mocks()
    _mock_pages(direct_vm, "GenLayer Season 2 points program has ended.")
    direct_vm.mock_llm(
        r".*",
        json.dumps(
            {
                "verdict": "refuted",
                "quote": "GenLayer Season 2 points program has ended.",
                "source": URLS,
            }
        ),
    )
    contract.attest(CLAIM, URLS)
    assert contract.verdict(CLAIM)["verdict"] == "refuted"
    assert contract.claims() == [CLAIM.lower()]


def test_empty_claim_is_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("[EXPECTED]"):
        contract.attest("   ", URLS)


def test_http_url_is_rejected(direct_vm, direct_deploy):
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("[EXPECTED]"):
        contract.attest(CLAIM, "http://docs.genlayer.com/developers/networks")


def test_verdict_outside_the_enum_is_an_llm_error(direct_vm, direct_deploy):
    _mock_pages(direct_vm)
    direct_vm.mock_llm(
        r".*",
        json.dumps(
            {
                "verdict": "definitely true!!",
                "quote": "GenLayer Season 2 points program is open.",
                "source": URLS,
            }
        ),
    )
    contract = direct_deploy(CONTRACT)
    with direct_vm.expect_revert("[LLM_ERROR]"):
        contract.attest(CLAIM, URLS)


def test_a_source_we_never_supplied_is_replaced_not_stored(direct_vm, direct_deploy):
    _mock_pages(direct_vm)
    direct_vm.mock_llm(
        r".*",
        json.dumps(
            {
                "verdict": "supported",
                "quote": "GenLayer Season 2 points program is open.",
                "source": "https://evil.example.com/not-ours",
            }
        ),
    )
    contract = direct_deploy(CONTRACT)
    contract.attest(CLAIM, URLS)
    stored = contract.verdict(CLAIM)["source"]
    assert stored == URLS
    assert "evil.example.com" not in stored
