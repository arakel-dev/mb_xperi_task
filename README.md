This is my solution to the Xperi Take-Home task.

### Notes and explanation on the logic of the app:

1. User initiates the request to **/search** endpoint with `?title="query"` parameter, the endpoint initiates main function from search.py module to find the best match to user's request.
2. Successful finds get saved into *tracks* table, and may be returned as a response to future queries, in order to omit duplicates and lower the number of API calls to external system.
3. If the user sends a query previously unknown to the database - this is when MusicBrainz API gets called with `strict=True`, `limit=100` parameter. If no result met the search criteria within first 100 results, go to next 100 (if there are) and repeat until `total_limit` is reached (default=500).
4. In order to be delivered to user as a result to his query, a recording needs to meet the following criteria:
 - The `artist is` Imagine Dragons (can be changed in options).
 - Contains `length` attribute.
 - The title/Album do not contain any of the `stop_words` specified in options.
 - Has to have an `album specified`.
 - The album has to be `part of official_discography` (fetched by separate function. The function should be in class Search, but for development I put it outside to save time on requests to MB API)

An artist `official_discography` has the following criteria:
 - Album `type` one of ("Album", "EP", "Single", "Demo") - can be changed within options.
 - Album `title` does not include any of the stop words (can be specified in options)
 - Artist `name` matches the one specified in options.
 - Contains `first-release-date` parameter.
 - Release status must be `Official`
 Albums in the official_discography are sorted by the value of first_release_date.

### The endpoint defines 4 types of answers:
 - `204 NO CONTENT FOUND` - If no content met the internal criteria, or there was empty/no response from MusicBrainz.
 - `201 CREATED` - If the call to MusicBrainz returned an entry that satisfied search criteria, and after this entry was successfuly saved within database table *tracks*.
 - `200 OK` - If current query has been successfully processed in the past and the algorithm found desired information within table *tracks*.


### Overall, the application consists of the following:
1. FastAPI endpoint /search that initiates the search with user input parameter ?title=
2. A search.py module containing Search class definition, and a 'lookup' main function guiding the logic behind returned response.
3. Database consists of 2 tables: *searches* and *tracks*. Table definitions can be found in sql.py module - interactions with database are consolidated here.
4. test_main.py is based on SQLAlchemy TESTClient that relies on pytest and httpx. There are 3 main test functions asserting http_status_code returned to the user. Each test has been .parametrize() with multiple (user query, expected status_code) pairs, 58 tests in total.
5. Dockerfile with configuration of Python application.
6. Docker-compose.yml file specifying structure of services for this application (Python API and default PostgreSQL server).

All Python files were documented to explain processing algorithm of this MusicBrainz processing API.

### In order to run on your machine:

1. Make sure docker and docker-compose are installed.
2. Enter shell and clone this repo into desired folder, cd into folder.
3. run docker-compose up --build, once the containers are up you should be able to connect to the application using http://0.0.0.0:8080 or localhost:8080 (on Windows)
4. docker exec -it fast-api "/bin/bash" to enter into new container, run pytest to run the tests.
5. Explore database by docker exec -it mb_db "/bin/bash" to enter container running PostgreSQL server, and run 'psql' to start interacting with the database.

There is also an online version running on GCP: http://34.172.97.135:8080/. But it requires some more work to get Monitoring features up.
