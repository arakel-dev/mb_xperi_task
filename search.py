import musicbrainzngs
import time
import bisect
import datetime as dt
from typing import List, Tuple
from sql import db_session, db_put_search, db_update_search, db_retrieve_track, db_put_track

options = {
    "artist": "Imagine Dragons",
    "discography_includes": ("Album", "EP", "Single", "Demo"),
    "discography_excludes": {"live", "remix", "itunes", "spotify"},
    "search_step": 100,
    "initial_offset": 0,
    "total_limit": 1000
}


def fetch_discography(artist_name: str, include: tuple, exclude: tuple) -> List[str]:
    """
    Get a list of albums released by artist_name, sorted by first release date

    :param artist_name: A string used to call for MB API search_release_groups
    :param include: A tuple of strings representing types of release-groups that contain official recordings/tracks
    :param exclude: A tuple of strings representing stop-words that should not be included in official discography

    :return: A list of strings (album names) previously sorted by first release date
    """
    albums_list = list()
    allowed_album_types = include
    stop_words = exclude

    raw_api_response = musicbrainzngs.search_release_groups(query=f"{artist_name}",
                                                            artistname=artist_name,
                                                            strict=True,
                                                            limit=100)
    for raw_release_group in raw_api_response["release-group-list"]:
        album_type_allowed = raw_release_group.get("type") in allowed_album_types
        if not album_type_allowed:
            continue

        includes_stop_words = any((word.lower() in raw_release_group.get("title").lower() for word in stop_words))
        if includes_stop_words:
            continue

        first_release_date = raw_release_group.get("first-release-date")[:]
        for release in raw_release_group["release-list"]:
            includes_stop_words = any((word.lower() in release.get("title").lower() for word in stop_words))
            if includes_stop_words:
                continue
            if release.get("status") != 'Official':
                continue
            bisect.insort(albums_list, (first_release_date, release.get("title")), lo=0)

    clean_albums_list = list()
    [clean_albums_list.append(item[1]) for item in albums_list if item[1] not in clean_albums_list]
    return clean_albums_list


class Search:
    musicbrainzngs.set_useragent(app="testing_musicbrainz",
                                 version="0.9",
                                 contact="Victor")
    default_artist = options.get("artist")
    album_types = options.get("discography_includes")
    stop_words = options.get("discography_excludes")
    artist_discography = fetch_discography(artist_name=default_artist, include=album_types, exclude=stop_words)
    initial_offset = options.get("initial_offset")
    default_step = options.get("search_step")
    search_limit = options.get("total_limit")
    _session = db_session()

    def __init__(self, query: str,
                 by_artist: str = default_artist):
        self.artist_name = by_artist
        self.query = query
        self._id, self.existing_reference_id = self.put_search_in_db()

        if self.existing_reference_id:
            self.track_bdid = self.existing_reference_id
            self.title, self.artist_name, self.album, self.length = self.quick_find()
        else:
            self.title, self.album, self.length, self.track_bdid = [False]*4

    def __str__(self):
        """
        String representation of a Search object

        :return: A String formatted as per task description
        """
        if any((not self.title,
                not self.artist_name,
                not self.album,
                not self.length)):
            return f"Query \'{self.query}\' was not processed correctly."

        return ", ".join([self.title, self.artist_name, self.album, self.length])

    def put_search_in_db(self) -> bool:
        """
        Calls database module function to insert new entry into searches table.

        :return: True if new entry was successfully inserted into the table, False if process failed.
        """
        return db_put_search(search_session=self._session,
                             search_query=self.query)

    def put_track_in_db(self) -> bool:
        """
        Calls database module function to insert new entry into tracks table

        :return: True if new entry was successfully inserted into the table, False if process failed.
        """
        try:
            self.track_bdid = db_put_track(self._session, self.title, self.artist_name, self.album, self.length)
            return True
        except Exception as e:
            return False

    def update_search_with_track_bdid(self) -> bool:
        """
        Calls database module function to update existing entry with a track_id created during by put_track_in_db().

        :return: True if new entry was successfully updated, False if process failed.
        """
        return db_update_search(search_session=self._session,
                                search_id=self._id,
                                track_bdid=self.track_bdid)

    def quick_find(self) -> Tuple[str]:
        """
        Calls database module to select an entry with track_id == existing_reference_id

        This method is  used when user's query has a duplicate within searches table that has track_bdid as not empty

        :return: Tuple of strings (Title, Artist, Album, Length)
        """
        return db_retrieve_track(search_session=self._session,
                                 existing_reference_id=self.existing_reference_id)

    def close(self):
        """
        Commits all pending updates, if any, then closes the database session.

        :return: False on success
        """
        self._session.commit()
        return self._session.close()

    def process_raw_recording_list(self, raw_recording_list: list) -> bool:
        """
        Process a response from musicbrainzngs.search_recordings(), one by one. When criteria is met -> return True

        For each entry from MB's response, check if:
        - recording contains length field
        - 'artist-credit-phrase' matches artist_name of a current Search object
        - title of current recording contains any of the words from stop-words set
        - the release is attached to current recording, and is within official_discography of a current Search object

        :param raw_recording_list: A raw list of recordings sent as part of response by MB.search_recordings() method

        :return: True upon assigning title, artist_name, album and length to current Search object, False otherwise
        """
        for raw_record in raw_recording_list:
            if not raw_record.get("length"):
                continue
            raw_length = dt.timedelta(milliseconds=int(raw_record.get("length")))

            if raw_record.get("artist-credit-phrase") != self.artist_name:
                continue
            raw_artist_name = raw_record.get("artist-credit-phrase")

            if any((word in raw_record.get("title").lower() for word in self.stop_words)):
                continue
            raw_title = raw_record.get("title")
            if "release-list" not in raw_record.keys():
                continue
            album_from_discography = any((release.get("title") in self.artist_discography
                                          for release in raw_record["release-list"]))
            if not album_from_discography:
                continue
            for release in raw_record["release-list"]:
                if release.get("title") not in self.artist_discography:
                    continue
                album_from_discography = release.get("title")
                break
            if not isinstance(album_from_discography, str):
                continue

            self.title = raw_title
            self.artist_name = raw_artist_name
            self.album = album_from_discography
            self.length = ':'.join(str(raw_length).split(':')[-2:]).split('.')[0]

            return True
        return False

    def call_mb(self) -> bool:
        """
        Call MB's API recordings endpoint to get a list of raw entries possible results to user's input.

        :return: True if any of the received entries met the processing criteria fully, False otherwise.
        """
        offset = self.initial_offset
        step = self.default_step
        limit = self.search_limit

        while True:
            time.sleep(1)
            raw_api_response = musicbrainzngs.search_recordings(query=f"{self.query}",
                                                                artistname=self.artist_name,
                                                                strict=True,
                                                                limit=step,
                                                                offset=offset)

            if self.process_raw_recording_list(raw_api_response["recording-list"]):
                return True

            offset += step
            if any((raw_api_response["recording-count"] <= offset,
                   offset >= limit)):
                break

        return False


def lookup(title: str):
    """
    Called by FastAPI endpoint when user initiates search session with title as their search query

    Step 1. Initiate new Search object and PostgreSQL session, insert new entry into searches database table,
    and assign default parameters as per logic defined in Search __init__() function.
    Step 2. Check if Step 1 found this search as new or duplicate in database:
        If it's a duplicate of an entry that successfully returned track before:
            - Update search object accordingly
            - Close database session
            - Return 200 and previously found track info from database.
        If it's a new entry:
            - Call MusicBrainz API and process results.
            - Return 204 if no results were returned, close db session.
            - Return 204 if no results met the criteria, or there was an error during processing, close db session.
            - Return 201 and new track info as string after inserting new track into db, updating current search in db.
            - Close db session.

    :param title: User's input query
    :return: x_string: A string formatted to met hometask description criteria.
             http_status code: A value presenting one of the possible outcomes during function execution.
    """
    search = Search(query=f"{title}")
    if search.track_bdid and search.update_search_with_track_bdid():
        x_string = search.__str__()
        search.close()
        return x_string, 200

    if not search.call_mb():
        x_string = search.__str__()
        search.close()
        return x_string, 204

    search.put_track_in_db()
    search.update_search_with_track_bdid()
    search.close()

    x_string = search.__str__()
    time.sleep(1)
    if "was not processed" in x_string:
        return x_string, 204

    return x_string, 201

if __name__ == "__main__":
    db_session()