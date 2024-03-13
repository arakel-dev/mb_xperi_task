from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Column, Integer, DateTime, Text
from datetime import datetime

Base = declarative_base()


class Track(Base):
    __tablename__ = 'tracks'

    track_id = Column(Integer(), nullable=False, primary_key=True)
    created_on = Column(DateTime(), nullable=False, default=datetime.now)
    title = Column(Text(), nullable=False, unique=False)
    artist = Column(Text(), nullable=False, unique=False)
    album = Column(Text(), nullable=False, unique=False)
    length = Column(Text(), nullable=False, unique=False)


class Search(Base):
    __tablename__ = 'searches'

    search_id = Column(Integer(), nullable=False, primary_key=True)
    created_on = Column(DateTime(), nullable=False, default=datetime.now)
    query = Column(Text(), nullable=False)
    track_id_ref = Column(Integer(), nullable=True)


def db_session():
    """
    Establish connection to a database and return a database session to work with on database-related tasks.

    :return: An SQLAlchemy sessionmaker Session object to interact with PostgreSQL database
    """
    db_url = URL.create(
        drivername='postgresql',
        username='postgres',
        password="postgres_user",
        host='mb_db',
        port=5432,
        database='postgres'
    )
    # Write with statement
    db_engine = create_engine(db_url)
    with db_engine.connect():
        session = sessionmaker(bind=db_engine)
        session = session()

        Base.metadata.create_all(db_engine)
        return session


def db_put_search(search_session, search_query):
    """
    Initiated every time new Search object is instantiated.
    Insert initiated Search into searches database, return track_ref_bdid if the Search entry is duplicate.

    Step 1. Check if an entry exists within searches database where query == (current) search_query
            If such an entry exists: - assign track_ref_bdid if it exists
                                     - assign False to track_ref_bdid if it doesn't exist
    Step 2. Create new Search database object and add to current db session.
    Step 3. Flush and refresh databasesession to confirm insertion by getting a search_id Serial key.

    :param search_session: A sessionmaker Session object created by db_session() function
    :param search_query: An initial string input from user
    :return: search_id: A Serial primary key of a newly created entry in searches table
             track_ref_bdid: A Serial primary key of a Track from tracks table that correspond to an original search_id
    """
    query_existed = False
    try:
        query_existed = search_session.query(Search).filter(Search.query == search_query).first()
        query_existed = query_existed.track_id_ref
    except AttributeError as ve:
        query_existed = False
    finally:
        track_ref_bdid = query_existed

    insert_search = Search(query=search_query)
    search_session.add(insert_search)

    search_session.flush()
    search_session.refresh(insert_search)
    search_session.commit()
    return insert_search.search_id, track_ref_bdid


def db_update_search(search_session, search_id, track_bdid):
    """
    Update an entry from searches table to include corresponding track_bdid from tracks table as track_id_ref.

    :param search_session: A sessionmaker Session object created by db_session() function.
    :param search_id: A Serial key of an entry from searches table.
    :param track_bdid: A Serial key of an entry from track table.
    :return: True on successful update, False otherwise.
    """
    try:
        current_entry = search_session.query(Search).filter(Search.search_id == search_id).first()

        current_entry.track_id_ref = track_bdid
        search_session.flush()
        search_session.commit()
    except Exception as e:
        return False
    return True


# Inserting new Track into the 'tracks' table and returning its serial key upon success.
def db_put_track(search_session, title, artist, album, length):
    """
    Insert new Track into tracks db after successful processing.
    Step 1. Check if an Entry exists containing the same parameters. Return track_id if such entry exists.
    Step 2. Create new Track object using function parameters.
    Step 3. Flush and refresh database session to confirm insertion by getting a track_id Serial key.

    :param search_session: A sessionmaker Session object created by db_session() function.
    :param title: A string containing recording's title.
    :param artist: A string containing recording's artist.
    :param album: A string containing recording's album.
    :param length: A string containing recording's length.

    :return: A Serial key of an existing entry in tracks database
    """
    try:
        existing_track = search_session.query(Track).filter(Track.title == title,
                                                            Track.album == album).one()
        return existing_track.track_id
    except NoResultFound as unique_entry:
        new_track = Track(title=title,
                          artist=artist,
                          album=album,
                          length=length)
        search_session.add(new_track)

        search_session.flush()
        search_session.refresh(new_track)
    return new_track.track_id


def db_retrieve_track(search_session, existing_reference_id):
    """
    Retrieve Title, Artist, Album and Length of existing entry from tracks table.

    :param search_session: A sessionmaker Session object created by db_session() function.
    :param existing_reference_id: A Serial key of desired table entry.
    :return: title: A string containing recording's title.
    :return: artist: A string containing recording's artist.
    :return: album: A string containing recording's album.
    :return: length: A string containing recording's length.
    """
    quick_find = search_session.query(Track).filter(Track.track_id == existing_reference_id).one()

    return quick_find.title, quick_find.artist, quick_find.album, quick_find.length

