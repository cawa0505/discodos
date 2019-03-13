from discodos.utils import *
from abc import ABC, abstractmethod
from discodos import log, db
from tabulate import tabulate as tab

# mix class (abstract)
class Mix (ABC):

    def __init__(self, db_conn, mix_name_or_id):
        self.db_conn = db_conn
        self.name_or_id = mix_name_or_id
        self.id_existing = False
        self.name_existing = False
        if is_number(mix_name_or_id):
            self.id = mix_name_or_id
            # if it's a mix-id, get mix-name and info
            try:
                self.info = db.get_mix_info(self.db_conn, self.id)
                # FIXME info should also be available as single attrs: created, venue, etc.
                self.name = self.info[1]
                self.id_existing = True
            except:
                log.info("Mix ID is not existing yet!")
                #raise Exception # use this for debugging
                #raise SystemExit(1)
        else:
            self.name = mix_name_or_id
            # if it's a mix-name, get the id unless it's "all"
            # (default value, should only show mix list)
            if not self.name == "all":
                try:
                    mix_id_tuple = db.get_mix_id(db_conn, self.name)
                    log.info('%s', mix_id_tuple)
                    self.id = mix_id_tuple[0]
                    self.id_existing = True
                    self.name_existing = True
                    # load basic mix-info from DB
                    # FIXME info should also be available as single attrs: created, venue, etc.
                    # FIXME or okay? here we assume mix is existing and id could be fetched
                    try:
                        self.info = db.get_mix_info(self.db_conn, self.id)
                    except:
                        log.info("Can't get mix info.")
                        #raise Exception # use this for debugging
                except:
                    log.info("Can't get mix-name from id. Mix not existing yet?")
                    #raise Exception # use this for debugging
                    #raise SystemExit(1)


    def create(self):
        if is_number(self.name_or_id):
            log.error("Mix name can't be a number!")
        else:
            print_help("Creating new mix \"{}\".".format(self.name))
            answers = self._create_ask_details()
            created_id = db.add_new_mix(self.db_conn, self.name, answers['played'], answers['venue'])
            self.db_conn.commit()
            # FIXME print_help should be a general help output tool, eg also for Mix_gui child,
            # thus it should be abstract here and must be overridden in child class
            print_help("New mix created with ID {}.".format(created_id))
            self.view_mixes_list()

    def add_track_from_db(self, release, track_no, pos = False):
        """
         release_dict_db and release_dict_discogs look a little different
         

        @param int pos : track position in mix
        @param release_dict_db release : a release_dict object returned from offline db: eg: found_in_db_releases[123456]
        @param string track_no : eg. A1, A2 
        @return  :
        @author
        """
        pass

    def add_track_from_discogs(self, release, track_no, pos = False):
        """
         release_dict_db and release_dict_discogs look a little different
         

        @param int pos : eg. 5 or 12
        @param release_dict_discogs release : eg. a releases_list + release_id index
e.g. found_releases[47114711]
        @param string track_no : e.g. A2 or A
        @return  :
        @author
        """
        pass

    def del_track(self, pos):
        pass

    def edit_track(self):
        pass

    def reorder_tracks(self, startpos = 1):
        pass

    def view(self, verbosity = "coarse"):
        """
         

        @param string verbosity : or fine
        @return tab :
        @author
        """
        pass

    def _add_track_to_db_wrapper(self, release_id, track_no, pos = False):
        """
         like in first version add_track_to_mix(conn, _mix_id, _track, _rel_list,
         _pos=None),
         also add_track_at_pos() schould be handled here.

        @param int release_id : simply the release_id, all figuring out stuff has been done before in add_track_discogs() or add_track_db()
        @param string track_no : eg A1, A2 as a string
        @return  :
        @author
        """
        pass

    @abstractmethod
    def _del_track_confirm(self, pos):
        pass

    @abstractmethod
    def _create_ask_details(self):
        pass

    @abstractmethod
    def _edit_track_ask_details(self):
        pass

    @abstractmethod
    def _view_tabulate(self):
        pass

    @abstractmethod
    def view_mixes_list(self):
        """
        view a list of all mixes in db


        @param
        @return
        @author
        """
        pass


# mix_cli child of mix class - cli specific stuff is handled here
class Mix_cli (Mix):

    def _del_track_confirm(self, pos):
        pass

    def _edit_track_ask_details(self):
        pass

    def _view_tabulate(self):
        pass

    def _create_ask_details(self):
        played = ask_user("When did you (last) play it? eg 2018-01-01 ")
        venue = ask_user(text="And where? ") 
        return {'played': played, 'venue': venue}

    def view_mixes_list(self):
        """
        view a list of all mixes in db


        @param
        @return
        @author
        """
        mixes_data = db.get_all_mixes(self.db_conn)
        tabulated = tab(mixes_data, tablefmt="simple",
                headers=["Mix #", "Name", "Created", "Updated", "Played", "Venue"])
        print_help(tabulated)
