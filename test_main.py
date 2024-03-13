
import pytest
from fastapi.testclient import TestClient
from app import app

"""
Test_main.py contains a test function for loading homepage, and 3 test functions to test functionality of the app.
Each of the 3 tests has been .parametrize() with a list containing pairs of (query, expected_status_code).
Lists are named according to the expected http_status_code when asserting responses.
"""

existing_songs = ["Demons", "Amsterdam", "It's Time",
                  "Bad Liar", "Radioactive", "Monster",
                  "Polaroid", "Mouth of the River", "My Life",
                  "Natural", "Monday", "Machine",
                  "Love of Mine", "Love", "Every Night",
                  "Believer", "Thunder", "Whatever it Takes",
                  "Not Today", "Next to Me", "Fallen",
                  "Nothing Left to Say", "Tokyo", "Real Life",
                  "Cha-Ching", "Round and Round", "Cover Up"]

non_existing_songs = ["Back in Black", "Fed Up", "What's my age"]

tests_201 = ((test_song, 201) for test_song in existing_songs)
tests_200 = ((test_song, 200) for test_song in existing_songs)
tests_204 = ((test_song, 204) for test_song in non_existing_songs)

client = TestClient(app)


def test_load_main():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"homepage": True}


@pytest.mark.parametrize("test_input, x_status", tests_201)
def test_lookup_new_song(test_input, x_status):
    response = client.get(f"/search?title={test_input}")

    assert response.status_code == x_status


@pytest.mark.parametrize("test_input, x_status", tests_204)
def test_lookup_non_existing_song(test_input, x_status):
    response = client.get(f"/search?title={test_input}")

    assert response.status_code == x_status


@pytest.mark.parametrize("test_input, x_status", tests_200)
def test_lookup_quick_find(test_input, x_status):
    response = client.get(f"/search?title={test_input}")

    assert response.status_code == x_status
