# Written by Arno Bakker 
# see LICENSE.txt for license information
#
# Razvan Deaconescu, 2008:
#       * corrected problem when running in background
#       * added usage and print_version functions
#       * uses getopt for command line argument parsing

import sys
import time
import os
import getopt
from traceback import print_exc

from Tribler.__init__ import LIBRARYNAME
from Tribler.Core.API import *
from Tribler.Core.BitTornado.__init__ import version, report_email


def usage():
    print "Usage: python dirseeder.py [options] directory"
    print "Options:"
    print "\t--port <port>"
    print "\t-p <port>\t\tuse <port> to listen for connections"
    print "\t\t\t\t(default is random value)"
    print "\t--output <output-dir>"
    print "\t-o <output-dir>\t\tuse <output-dir for storing downloaded data"
    print "\t\t\t\t(default is current directory)"
    print "\t--version"
    print "\t-v\t\t\tprint version and exit"
    print "\t--help"
    print "\t-h\t\t\tprint this help screen"
    print
    print "Report bugs to <" + report_email + ">"

def print_version():
    print version, "<" + report_email + ">"

def states_callback(dslist):
    for ds in dslist:
        state_callback(ds)
    return (1.0, False)

def state_callback(ds):
    d = ds.get_download()
#    print >>sys.stderr,`d.get_def().get_name()`,dlstatus_strings[ds.get_status()],ds.get_progress(),"%",ds.get_error(),"up",ds.get_current_speed(UPLOAD),"down",ds.get_current_speed(DOWNLOAD)
    print >>sys.stderr, '%s %s %5.2f%% %s up %8.2fKB/s down %8.2fKB/s' % \
            (d.get_def().get_name(), \
            dlstatus_strings[ds.get_status()], \
            ds.get_progress() * 100, \
            ds.get_error(), \
            ds.get_current_speed(UPLOAD), \
            ds.get_current_speed(DOWNLOAD))

    return (1.0, False)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvo:p:", ["help", "version", "output-dir", "port"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    # init to default values
    output_dir = os.getcwd()
    port = 6969

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-o", "--output-dir"):
            output_dir = a
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-v", "--version"):
            print_version()
            sys.exit(0)
        else:
            assert False, "unhandled option"


    if len(args) > 1:
        print "Too many arguments"
        usage()
        sys.exit(2)
    elif len(args) == 0:
        torrentsdir = os.getcwd()
    else:
        torrentsdir = args[0]

    print "Press Ctrl-C to stop the download"

    # setup session
    sscfg = SessionStartupConfig()
    statedir = os.path.join(output_dir,"."+LIBRARYNAME)
    sscfg.set_state_dir(statedir)
    sscfg.set_listen_port(port)
    sscfg.set_megacache(False)
    sscfg.set_overlay(False)
    sscfg.set_dialback(False)
    sscfg.set_internal_tracker(True)
    
    s = Session(sscfg)
    s.set_download_states_callback(states_callback, getpeerlist=False)
    
    # Restore previous Session
    s.load_checkpoint()

    # setup and start downloads
    dscfg = DownloadStartupConfig()
    dscfg.set_dest_dir(output_dir);
    dscfg.set_max_speed(UPLOAD,256) # FOR DEMO
    
    for torrent_file in os.listdir(torrentsdir):
        if torrent_file.endswith(".torrent"): 
            try:
                tdef = TorrentDef.load(torrent_file)
                s.add_to_internal_tracker(tdef)
                d = s.start_download(tdef, dscfg)
            except DuplicateDownloadException, e:
                print >>sys.stderr,"Restarting existing Download"
            except Exception, e:
                print_exc()
    
    #
    # loop while waiting for CTRL-C (or any other signal/interrupt)
    #
    # - cannot use sys.stdin.read() - it means busy waiting when running
    #   the process in background
    # - cannot use condition variable - that don't listen to KeyboardInterrupt
    #
    # time.sleep(sys.maxint) has "issues" on 64bit architectures; divide it
    # by some value (2048) to solve problem
    #
    try:
        while True:
        #    time.sleep(sys.maxint/2048)
            data = sys.stdin.read()
            print >>sys.stderr,"len data",len(data)
            print >>sys.stderr,"data",`data`
            if len(data) == 0:
                break
    except Exception, e:
        print_exc()

    s.shutdown()
    while not s.has_shutdown():
        time.sleep(1)
    time.sleep(1)


if __name__ == "__main__":
    main()
