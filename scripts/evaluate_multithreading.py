import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.database import get_database_connection
from app.rag_service import answer_question


DATASET_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "multithreading_evaluation_dataset.json"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "multithreading_evaluation_report.json"
)


# --------------------------------------------------
# Text helpers
# --------------------------------------------------

def normalize_text(value: str) -> str:
    """
    Normalize text before keyword comparison.
    Ignores capitalization, Markdown and punctuation.
    """

    value = value.lower()
    value = value.replace("²", "^2")

    value = re.sub(
        r"[`*_\"'“”‘’()\[\]{}#]",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()

def contains_keyword(
    answer: str,
    keyword: str,
) -> bool:
    normalized_answer = normalize_text(answer)
    normalized_keyword = normalize_text(keyword)

    return normalized_keyword in normalized_answer


# --------------------------------------------------
# Database helpers
# --------------------------------------------------

def find_document_id(
    filename: str,
) -> int | None:
    """
    Find the newest ready document matching
    the filename from the evaluation dataset.
    """

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM documents
                WHERE filename = %s
                  AND status = 'ready'
                ORDER BY id DESC
                LIMIT 1;
                """,
                (filename,),
            )

            row = cursor.fetchone()

    if row is None:
        return None

    return int(row[0])


# --------------------------------------------------
# Evaluation checks
# --------------------------------------------------

def evaluate_keyword_groups(
    answer: str,
    keyword_groups: list[list[str]],
) -> dict[str, Any]:
    """
    Every keyword group must have at least
    one matching keyword.

    Example group:
    ["10 cm", "10"]

    The answer passes this group if either
    value appears.
    """

    if not keyword_groups:
        return {
            "passed": True,
            "matched_groups": 0,
            "total_groups": 0,
            "group_results": [],
        }

    group_results = []
    matched_groups = 0

    for group in keyword_groups:
        matched_keywords = [
            keyword
            for keyword in group
            if contains_keyword(
                answer,
                keyword,
            )
        ]

        group_passed = bool(matched_keywords)

        if group_passed:
            matched_groups += 1

        group_results.append(
            {
                "accepted_keywords": group,
                "matched_keywords": matched_keywords,
                "passed": group_passed,
            }
        )

    total_groups = len(keyword_groups)

    return {
        "passed":
            matched_groups == total_groups,
        "matched_groups":
            matched_groups,
        "total_groups":
            total_groups,
        "group_results":
            group_results,
    }


def detects_refusal(answer: str) -> bool:
    """
    Detect whether the chatbot correctly says
    that the requested information is not
    available in the uploaded document.
    """

    refusal_phrases = [
        "could not find",
        "couldn't find",
        "cannot find",
        "can't find",
        "not found in the document",
        "not available in the document",
        "not included in the document",
        "not mentioned in the document",
        "not provided in the document",
        "does not contain",
        "doesn't contain",
        "outside the document",
        "outside the provided context",
        "uploaded document does not",
        "provided document does not",
        "based on the provided document",
        "insufficient information",
    ]

    normalized_answer = normalize_text(answer)

    return any(
        phrase in normalized_answer
        for phrase in refusal_phrases
    )


def extract_similarity_scores(
    sources: list[dict[str, Any]],
) -> list[float]:
    scores = []

    for source in sources:
        try:
            scores.append(
                float(
                    source.get(
                        "similarity",
                        0,
                    )
                )
            )
        except (TypeError, ValueError):
            continue

    return scores


def calculate_average(
    values: list[float],
) -> float:
    if not values:
        return 0.0

    return sum(values) / len(values)


# --------------------------------------------------
# Individual test case
# --------------------------------------------------

def evaluate_test_case(
    test_case: dict[str, Any],
    document_id_cache: dict[str, int],
) -> dict[str, Any]:
    question = test_case["question"]

    question_type = test_case[
        "question_type"
    ]

    filename = test_case[
        "document_filename"
    ]

    document_id = document_id_cache[
        filename
    ]

    print()
    print("=" * 70)
    print(
        f"Test {test_case['id']}: "
        f"{question}"
    )
    print("=" * 70)

    try:
        result = answer_question(
            question=question,
            document_ids=[document_id],
        )

        answer = result.get(
            "answer",
            "",
        )

        sources = result.get(
            "sources",
            [],
        )

        similarity_scores = (
            extract_similarity_scores(
                sources
            )
        )

        average_similarity = (
            calculate_average(
                similarity_scores
            )
        )

        highest_similarity = (
            max(similarity_scores)
            if similarity_scores
            else 0.0
        )

        keyword_evaluation = (
            evaluate_keyword_groups(
                answer,
                test_case.get(
                    "required_keyword_groups",
                    [],
                ),
            )
        )

        refusal_detected = (
            detects_refusal(answer)
        )

        source_found = len(sources) > 0

        if question_type == "answerable":
            answer_passed = (
                keyword_evaluation["passed"]
                and not refusal_detected
            )

            # Answer correctness is most important.
            score = 0

            if answer_passed:
                score += 70

            if source_found:
                score += 20

            if highest_similarity >= 0.30:
                score += 10

        else:
            # Unsupported questions should be refused.
            answer_passed = refusal_detected
            score = 100 if answer_passed else 0

        status = (
            "PASS"
            if answer_passed
            else "FAIL"
        )

        print(f"Result: {status}")
        print(f"Score: {score}/100")
        print(
            "Highest similarity: "
            f"{highest_similarity:.4f}"
        )
        print(
            "Sources returned: "
            f"{len(sources)}"
        )

        print()
        print("Answer:")
        print(answer)

        return {
            "id": test_case["id"],
            "question": question,
            "question_type": question_type,
            "document_filename": filename,
            "document_id": document_id,
            "status": status,
            "passed": answer_passed,
            "score": score,
            "refusal_detected":
                refusal_detected,
            "source_found":
                source_found,
            "source_count":
                len(sources),
            "highest_similarity":
                round(
                    highest_similarity,
                    4,
                ),
            "average_similarity":
                round(
                    average_similarity,
                    4,
                ),
            "keyword_evaluation":
                keyword_evaluation,
            "answer": answer,
            "sources": sources,
            "error": None,
        }

    except Exception as error:
        print("Result: ERROR")
        print(f"Error: {error}")

        return {
            "id": test_case["id"],
            "question": question,
            "question_type": question_type,
            "document_filename": filename,
            "document_id": document_id,
            "status": "ERROR",
            "passed": False,
            "score": 0,
            "refusal_detected": False,
            "source_found": False,
            "source_count": 0,
            "highest_similarity": 0,
            "average_similarity": 0,
            "keyword_evaluation": None,
            "answer": None,
            "sources": [],
            "error": str(error),
        }


# --------------------------------------------------
# Report summary
# --------------------------------------------------

def create_summary(
    test_results: list[dict[str, Any]],
) -> dict[str, Any]:
    total_tests = len(test_results)

    passed_tests = sum(
        1
        for result in test_results
        if result["passed"]
    )

    failed_tests = sum(
        1
        for result in test_results
        if not result["passed"]
    )

    answerable_results = [
        result
        for result in test_results
        if result["question_type"]
        == "answerable"
    ]

    unanswerable_results = [
        result
        for result in test_results
        if result["question_type"]
        == "unanswerable"
    ]

    answerable_passed = sum(
        1
        for result in answerable_results
        if result["passed"]
    )

    unanswerable_passed = sum(
        1
        for result in unanswerable_results
        if result["passed"]
    )

    total_score = sum(
        result["score"]
        for result in test_results
    )

    maximum_score = total_tests * 100

    overall_percentage = (
        total_score / maximum_score * 100
        if maximum_score
        else 0
    )

    answer_accuracy = (
        answerable_passed
        / len(answerable_results)
        * 100
        if answerable_results
        else 0
    )

    refusal_accuracy = (
        unanswerable_passed
        / len(unanswerable_results)
        * 100
        if unanswerable_results
        else 0
    )

    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "overall_score_percentage":
            round(overall_percentage, 2),
        "answerable_questions": {
            "total":
                len(answerable_results),
            "passed":
                answerable_passed,
            "accuracy_percentage":
                round(answer_accuracy, 2),
        },
        "unanswerable_questions": {
            "total":
                len(unanswerable_results),
            "correctly_refused":
                unanswerable_passed,
            "refusal_accuracy_percentage":
                round(refusal_accuracy, 2),
        },
    }


# --------------------------------------------------
# Main evaluator
# --------------------------------------------------

def run_evaluation() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as dataset_file:
        test_cases = json.load(
            dataset_file
        )

    if not test_cases:
        raise ValueError(
            "The evaluation dataset is empty."
        )

    print()
    print("MULTI-THREADING PDF RAG EVALUATION")
    print("-" * 70)
    print(
        f"Number of tests: "
        f"{len(test_cases)}"
    )

    filenames = {
        test_case["document_filename"]
        for test_case in test_cases
    }

    document_id_cache = {}

    for filename in filenames:
        document_id = find_document_id(
            filename
        )

        if document_id is None:
            raise ValueError(
                "Ready document not found: "
                f"{filename}"
            )

        document_id_cache[filename] = (
            document_id
        )

        print(
            f"Using document: {filename} "
            f"(ID: {document_id})"
        )

    test_results = []

    for test_case in test_cases:
        result = evaluate_test_case(
            test_case,
            document_id_cache,
        )

        test_results.append(result)

    summary = create_summary(
        test_results
    )

    report = {
        "evaluation_name":
            "Multi-Threading PDF RAG Evaluation",
        "created_at":
            datetime.now().isoformat(),
        "dataset_path":
            str(DATASET_PATH),
        "summary":
            summary,
        "test_results":
            test_results,
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REPORT_PATH.open(
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            report,
            report_file,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("=" * 70)
    print("FINAL MULTI-THREADING RESULTS")
    print("=" * 70)
    print(
        f"Passed: "
        f"{summary['passed_tests']}/"
        f"{summary['total_tests']}"
    )
    print(
        "Answerable-question accuracy: "
        f"{summary['answerable_questions']['accuracy_percentage']}%"
    )
    print(
        "Unsupported-question refusal accuracy: "
        f"{summary['unanswerable_questions']['refusal_accuracy_percentage']}%"
    )
    print(
        "Overall score: "
        f"{summary['overall_score_percentage']}%"
    )
    print()
    print(
        "Detailed report saved to:"
    )
    print(REPORT_PATH)


if __name__ == "__main__":
    run_evaluation()
