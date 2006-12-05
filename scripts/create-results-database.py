#!/usr/bin/env python

########################################################################
#
# File:   create-results-database.py
# Author: Nathaniel Smith
# Date:   2003-07-02
#
# Contents:
#   Script to set up a PostgreSQL results database.
#
# Copyright (c) 2003 by CodeSourcery, LLC.  All rights reserved. 
#
# For license terms see the file COPYING.
#
########################################################################

########################################################################
# Imports
########################################################################

import sys
import pgdb

########################################################################
# Script
########################################################################

if len(sys.argv) != 2:
    print "Usage: %s <database_name>" % (sys.argv[0],)
    sys.exit(1)

dbname = sys.argv[1]
cxn = pgdb.connect(database=dbname)
cursor = cxn.cursor()

cursor.execute("""
    CREATE TABLE db_schema_version (
        version INT
    )
    """)
cursor.execute("""
    INSERT INTO db_schema_version (version) VALUES (1)
    """)

cursor.execute("""
    CREATE SEQUENCE run_id_seq
    """)

cursor.execute("""
    CREATE TABLE runs (
        run_id INT PRIMARY KEY
    )
    """)

cursor.execute("""
    CREATE TABLE run_annotations (
        run_id INT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs (run_id),
        PRIMARY KEY (run_id, key)
    )
    """)
        
cursor.execute("""
    CREATE TABLE results (
        run_id INT NOT NULL,
        result_id TEXT NOT NULL,
        kind TEXT NOT NULL,
        outcome TEXT NOT NULL,
        FOREIGN KEY (run_id) REFERENCES runs (run_id),
        PRIMARY KEY (run_id, result_id, kind)
    )
    """)
cursor.execute("""
    CREATE INDEX results_outcome_idx ON results (run_id, outcome)
    """)
cursor.execute("""
    CREATE INDEX results_kind_idx ON results (run_id, kind)
    """)

cursor.execute("""
    CREATE TABLE result_annotations (
        run_id INT NOT NULL,
        result_id TEXT NOT NULL,
        result_kind TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        FOREIGN KEY (run_id, result_id, result_kind)
            REFERENCES results (run_id, result_id, kind),
        PRIMARY KEY (run_id, result_id, result_kind, key)
    )
    """)

cxn.commit()

########################################################################
# Local Variables:
# mode: python
# indent-tabs-mode: nil
# fill-column: 72
# End:
