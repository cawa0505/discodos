#!/usr/bin/env python

from discodos.utils import ask_user, print_help, Config
from discodos.views import User_int
from discodos.ctrls import Mix_ctrl_cli, Coll_ctrl_cli
from discodos import log
import argparse
import sys
import pprint

# argparser init
def argparser(argv):
    parser = argparse.ArgumentParser(
                 formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
		"-v", "--verbose", dest="verbose_count",
        action="count", default=0,
        help="increase log verbosity (-v -> INFO level, -vv DEBUG level)")
    parser.add_argument(
		"-o", "--offline", dest="offline_mode",
        action="store_true",
        help="doesn't connect to Discogs (most options work in on- and offline mode.")
    # basic subparser element:
    subparsers = parser.add_subparsers()
    ### SEARCH subparser #######################################################
    search_subparser = subparsers.add_parser(
        name='search',
        help='search for a Discogs release or track and optionally add it to a mix')
    search_subparser.add_argument(
        dest='release_search',
        help='search for this release name or ID')
    search_subparser.add_argument(
        "-m", "--mix", type=str, dest='add_to_mix',
        help='add found release to given mix ID (asks which track to add)', default=0)
    search_subparser.add_argument(
        "-t", "--track", type=str, dest='track_to_add',
        help='add this track number to mix (eg. A1, AA, B2, ...)', default=0)
    search_subparser.add_argument(
        "-p", "--pos", type=str, dest='add_at_pos',
        help='insert track at specific position in mix (eg. 01, 14, ...), defaults to next',
        default=0)
    ### MIX subparser #############################################################
    mix_subparser = subparsers.add_parser(
        name='mix',
        help='manage your mixes')
    mix_subparser.add_argument(
        dest='mix_name',
        help='''current mix (mix name or mix ID that should be displayed, edited, created, ...), 
                omit this argument to show an overview of available mixes.''',
        nargs='?',
        default='all')
    mix_subparser.add_argument(
        "-v", "--verbose",
        action="count", default=0,
        dest='verbose_tracklist',
        help='''mix tracklist shows more details (-v) or shows MusicBrainz
                "matching information" (-vv) - this also gives you links to Discogs
                releases, MusicBrainz releases/recordings and AccousticBrainz entries''')
    # only one of --create-mix OR --edit OR --add possible
    mix_subp_excl_group = mix_subparser.add_mutually_exclusive_group()
    mix_subp_excl_group.add_argument(
        "-c", "--create-mix", action='store_true',
        help='create a new mix')
    mix_subp_excl_group.add_argument(
        "-D", "--delete-mix", action='store_true',
        help='deletes a mix and all its contained tracks!')
    mix_subp_excl_group.add_argument(
        "-e", "--edit", type=str,
        dest='edit_mix_track',
        metavar='POSITION',
        help='add/edit rating, notes, key and other info of a track in a mix')
    mix_subp_excl_group.add_argument(
        "-E", "--edit-mix", action='store_true',
        help='edit general info about a mix (name, played date, venue)')
    mix_subp_excl_group.add_argument(
        "-b", "--bulk-edit", type=str,
        dest='bulk_edit',
        metavar='FIELD_LIST',
        help='''bulk-edit specific columns of whole mixes. Syntax of col list eg: <col1>,<col2>,...
        possible cols: key,bpm,track_no,track_pos,key_notes,trans_rating,trans_notes,release_id,notes''')
    mix_subp_excl_group.add_argument(
        "-a", "--add-to-mix", type=str,
        dest='add_release_to_mix',
        metavar='SEARCH_TERM',
        help='''search for release in collection and add it to current mix,
                SEARCH_TERM can also be a Discogs release ID''')
    mix_subp_excl_group.add_argument(
        "-r", "--reorder-tracks", type=int,
        dest='reorder_from_pos',
        metavar='POSITION',
        help='reorder tracks in current mix, starting at POSITION')
    mix_subp_excl_group.add_argument(
        "-d", "--delete-track", type=int,
        dest='delete_track_pos',
        metavar='POSITION',
        help='delete a track in current mix')
    mix_subp_excl_group.add_argument(
        "--copy", action='store_true',
        dest='copy_mix',
        help='creates new mix based on current mix_name (or ID)')
    mix_subp_excl_group.add_argument(
        "-u", "--discogs-update", action='store_true',
        dest='discogs_update',
        help='updates tracks in current mix with additional info from Discogs')
    mix_subp_excl_group.add_argument(
        "-z", "--brainz-update", action="count", default=0,
        dest='brainz_update',
        help='''updates tracks in current mix with additional info from MusicBrainz and AcousticBrainz.
        Leave out mix ID to update every track contained in a mix.
        -z quick match, -zz detailed match (takes longer, but more results)''')
    # mutually exclusive group ends here
    mix_subparser.add_argument(
        "-p", "--pos", type=int,
        dest='mix_mode_add_at_pos',
        help='add found release track at specific position in mix')
    ### SUGGEST subparser ##########################################################
    suggest_subparser = subparsers.add_parser(
        name='suggest',
        help='suggests track-combinations based on what you\'ve played before, BPM range and musical key')
    suggest_subparser.add_argument(
        dest='suggest_search',
        help='track or release name you want to show a "track-combination report" for.',
        nargs='?',
        default='0')
    suggest_subparser.add_argument(
        "-b", "--bpm", type=int,
        dest='suggest_bpm', metavar="BPM",
        help='suggests tracks based on BPM value, within a configurable pitch-range (default: +/-6 percent)')
    suggest_subparser.add_argument(
        "-k", "--key", type=str,
        dest='suggest_key', metavar="KEY",
        help='suggests tracks based on musical key')
    # only the main parser goes into a variable
    arguments = parser.parse_args(argv[1:])
    log.info("Console log_level currently set to {} via config.yaml or default".format(
        log.handlers[0].level))
    # Sets log level to WARN going more verbose for each new -v.
    cli_level = max(3 - arguments.verbose_count, 0) * 10
    if cli_level < log.handlers[0].level: # 10 = DEBUG, 20 = INFO, 30 = WARNING
        log.handlers[0].setLevel(cli_level)
        log.warning("Console log_level override via cli. Now set to {}.".format(
            log.handlers[0].level))
    return arguments 



# MAIN
def main():
    # CONFIGURATOR INIT / DISCOGS API conf
    conf = Config()
    log.handlers[0].setLevel(conf.log_level) # handler 0 is the console handler
    # SETUP / INIT
    #global args, ONLINE, user
    global args, user
    args = argparser(sys.argv)
    # DEBUG stuff
    #print(vars(args))
    log.info("args_dict: %s", vars(args))
    #log.info("dir(args): %s", dir(args))
    # check cli args and set attributes
    user = User_int(args)
    log.info("user.WANTS_ONLINE: %s", user.WANTS_ONLINE)
    # INIT COLLECTION CONTROLLER (DISCOGS API CONNECTION)
    coll_ctrl = Coll_ctrl_cli(False, user, conf.discogs_token, conf.discogs_appid,
            conf.discobase, conf.musicbrainz_user, conf.musicbrainz_password)

    #### RELEASE MODE
    if user.WANTS_TO_LIST_ALL_RELEASES:
        coll_ctrl.view_all_releases()
    elif user.WANTS_TO_SEARCH_FOR_RELEASE:
        searchterm = args.release_search
        if coll_ctrl.ONLINE:
            discogs_rel_found = coll_ctrl.search_release(searchterm)
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = Mix_ctrl_cli(False, args.add_to_mix, user, conf.discobase)
                mix_ctrl.add_discogs_track(discogs_rel_found, args.track_to_add,
                        args.add_at_pos,
                        track_no_suggest = coll_ctrl.first_track_on_release)
            else:
                print_help("Nothing more to do. Use -m <mix_name> to add to a mix.")
        else:
            database_rel_found = coll_ctrl.search_release(searchterm)
            if user.WANTS_TO_ADD_TO_MIX or user.WANTS_TO_ADD_AT_POSITION:
                mix_ctrl = Mix_ctrl_cli(False, args.add_to_mix, user, conf.discobase)
                mix_ctrl.add_offline_track(database_rel_found, args.track_to_add,
                        args.add_at_pos)
            else:
                print_help("Nothing more to do. Use -m <mix_name> to add to a mix.")


    ##### MIX MODE ########################################################
    ### NO MIX ID GIVEN ###################################################
    if user.WANTS_TO_SHOW_MIX_OVERVIEW:
        # we instantiate a mix controller object
        mix_ctrl = Mix_ctrl_cli(False, args.mix_name, user, conf.discobase)
        if user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(coll_ctrl,
              detail = user.BRAINZ_SEARCH_DETAIL)
        else:
            mix_ctrl.view_mixes_list()

    ### MIX ID GIVEN #############################################
    ### SHOW MIX DETAILS ##################################################
    elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
        log.info("A mix_name or ID was given. Instantiating Mix_ctrl_cli class.\n")
        mix_ctrl = Mix_ctrl_cli(False, args.mix_name, user, conf.discobase)
        #coll_ctrl = Coll_ctrl_cli(conn, user)
        ### CREATE A NEW MIX ##############################################
        if user.WANTS_TO_CREATE_MIX:
            mix_ctrl.create()
            # mix is created (or not), nothing else to do
            raise SystemExit(0)
        ### DELETE A MIX ##############################################
        if user.WANTS_TO_DELETE_MIX:
            mix_ctrl.delete()
            # mix is deleted (or not), nothing else to do
            raise SystemExit(0)
        ### DO STUFF WITH EXISTING MIXES ###################################
        ### EDIT A MIX-TRACK ###############################################
        if user.WANTS_TO_EDIT_MIX_TRACK:
            mix_ctrl.edit_track(args.edit_mix_track)
        ### REORDER TRACKLIST
        elif user.WANTS_TO_REORDER_MIX_TRACKLIST:
            print_help("Tracklist reordering starting at position {}".format(
                       args.reorder_from_pos))
            mix_ctrl.reorder_tracks(args.reorder_from_pos)
        ### DELETE A TRACK FROM MIX
        elif user.WANTS_TO_DELETE_MIX_TRACK:
            mix_ctrl.delete_track(args.delete_track_pos)
        ### SEARCH FOR A RELEASE AND ADD IT TO MIX (same as in release mode)
        elif user.WANTS_TO_ADD_RELEASE_IN_MIX_MODE:
            if mix_ctrl.mix.id_existing: # accessing a mix attr directly is bad practice
                if coll_ctrl.ONLINE:
                    # search_release returns an online or offline releases type object
                    # depending on the models online-state
                    discogs_rel_found = coll_ctrl.search_release(
                      args.add_release_to_mix)
                    mix_ctrl.add_discogs_track(discogs_rel_found, False,
                      args.mix_mode_add_at_pos,
                      track_no_suggest = coll_ctrl.first_track_on_release)
                else:
                    database_rel_found = coll_ctrl.search_release(
                            args.add_release_to_mix)
                    mix_ctrl.add_offline_track(database_rel_found, False,
                            args.mix_mode_add_at_pos)
            else:
                log.error("Mix not existing.")
        #### COPY A MIX
        elif user.WANTS_TO_COPY_MIX:
            mix_ctrl.copy_mix()
        #### EDIT MIX INFO
        elif user.WANTS_TO_EDIT_MIX:
            mix_ctrl.edit_mix()
                                       
        #### UPDATE TRACKS WITH DISCOGS INFO
        elif user.WANTS_TO_PULL_TRACK_INFO_IN_MIX_MODE:
            mix_ctrl.pull_track_info_from_discogs(coll_ctrl,
              start_pos=args.mix_mode_add_at_pos)
        #### UPDATE TRACKS WITH MUSICBRAINZ & ACOUSTICBRAINZ INFO
        elif user.WANTS_TO_PULL_BRAINZ_INFO_IN_MIX_MODE:
            mix_ctrl.update_track_info_from_brainz(coll_ctrl,
              start_pos=args.mix_mode_add_at_pos, detail=user.BRAINZ_SEARCH_DETAIL)


        #### BULK EDIT MIX COLUMNS
        elif user.WANTS_TO_BULK_EDIT:
            mix_ctrl.bulk_edit_tracks(args.bulk_edit, args.mix_mode_add_at_pos)

        #### JUST SHOW MIX-TRACKLIST:
        elif user.WANTS_TO_SHOW_MIX_TRACKLIST:
            #pretty_print_mix_tracklist(mix_ctrl.id, mix_ctrl.info)
            mix_ctrl.view()


    ### SUGGEST MODE (was TRACK MODE)
    #if user.WANTS_TO_PULL_TRACK_INFO:
    #    mix_ctrl = Mix_ctrl_cli(False, False, user, conf.discobase)
    #    mix_ctrl.pull_track_info_from_discogs(coll_ctrl)
    #elif user.WANTS_SUGGEST_TRACK_REPORT:
    if user.WANTS_SUGGEST_TRACK_REPORT:
        coll_ctrl.track_report(args.suggest_search)
    if user.WANTS_SUGGEST_BPM_REPORT:
        coll_ctrl.bpm_report(args.suggest_bpm, 6)
    if user.WANTS_SUGGEST_KEY_REPORT:
        coll_ctrl.key_report(args.suggest_key)

    if user.DID_NOT_PROVIDE_COMMAND:
        if not coll_ctrl.ONLINE:
            merr ='Connection to your Discogs Collection failed.'
            merr+='\nCheck your internet connection and DiscoDOS configuration (config.yaml)'
            merr+='\nBut anyway:'
            log.error(merr)
            coll_ctrl.cli.welcome_to_discodos()
            raise SystemExit(1)
        coll_ctrl.cli.welcome_to_discodos()
        m ='Connection to your Discogs Collection is working, '
        m+="but you didn't provide a command. Here are some things you could do:"
        m+='\n\nImport your Collection:'
        m+='\nsetup -i'
        m+='\n\nCreate a mix:'
        m+='\ndisco mix my_mix -c'
        m+='\n\nSearch in your collection and add tracks to the mix:'
        m+='\ndisco mix my_mix -a "search terms"'
        m+='\n\nView your mix. Leave out mix-name '
        m+='to view all your mixes:'
        m+='\ndisco mix my_mix'
        m+='\n\nDiscoDOS by default is minimalistic. The initial import only '
        m+='gave us release-titles/artists and CatNos. Now fetch track-names '
        m+='and track-artists:'
        m+='\ndisco mix my_mix -u'
        m+='\n\nMatch the tracks with MusicBrainz/AcousticBrainz and get '
        m+='BPM and musical key information (-z is quicker but not as accurate):'
        m+='\ndisco mix my_mix -zz'
        m+='\n\nIf you were lucky some tracks will show BPM and key information: '
        m+='(-v is a more detailed view, it includes eg track-names, bpm, key)'
        m+='\ndisco mix my_mix -v'
        m+='\n\nView weblinks pointing directly to your Discogs & MusicBrainz releases, '
        m+='find out more interesting details about your music via AcousticBrainz, '
        m+='and see how the actual matching went:'
        m+='\ndisco mix my_mix -vv'
        m+="\n\nIf a track couldn't be matched automatically, you could head to "
        m+='the MusicBrainz website, find a Recording MBID and put it in yourself:'
        m+='\ndisco mix my_mix -e 1'
        m+="\n\nThere's a lot more you can do. Each subcommand has it's own help command:"
        m+='\ndisco mix -h'
        m+='\ndisco search -h'
        m+='\ndisco suggest -h'
        m+="\nStill questions? Check out the README or open an issue on Github: "
        m+='https://github.com/JOJ0/discodos'
        print(m)

# __MAIN try/except wrap
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.error('Program interrupted!')
    #finally:
        #log.shutdown()
