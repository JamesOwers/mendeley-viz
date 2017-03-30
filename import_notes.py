#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reads a folder of .md files (with file name formatting of export_notes.pm)
and rewrites the mendeley sqlite database notes table with the corresponding
document_id notes
"""

from __future__ import print_function, division

__author__  = "James Owers"
__license__ = "MIT"
__version__ = "0.1"
__email__   = "james.owers@ed.ac.uk"
__status__  = "Development"

doc_name_str = '{citationKey} ({docid}) {title}'

import sqlite3
import os
import pandas as pd
import numpy as np
import sys
import argparse
import glob
import markdown2
import markdown

try:
    DATABASE_LOC = os.environ['MENDELEY_DATABASE_LOC']
except KeyError:
    msg = 'ERROR: ' + \
        'You must set a system environment variable MENDELEY_DATABASE_LOC ' +\
        'that points to the mendeley sqlite database instance. c.f' +\
        'http://support.mendeley.com/customer/en/portal/articles/227951-' +\
        'how-do-i-locate-mendeley-desktop-database-files-on-my-computer- ' +\
        'for location of the database. On unix machines you can set ' + \
        'environment variables by running `export MENDELEY_DATABASE_LOC' +\
        '=/path/to/database.sqlite`. You can add this command to your ' +\
        '~/.bash_profile such that this is run each time you log in to ' +\
        'your terminal.'
    print(msg, file=sys.stderr)
    raise

    
def diff_pd(df1, df2):
    """Identify differences between two pandas DataFrames"""
    assert (df1.columns == df2.columns).all(), \
        "DataFrame column names are different"
    if df1.equals(df2):
        return None
    else:
        # need to account for np.nan != np.nan returning True
        diff_mask = (df1 != df2) & ~(df1.isnull() & df2.isnull())
        ne_stacked = diff_mask.stack()
        changed = ne_stacked[ne_stacked]
        changed.index.names = ['id', 'col']
        difference_locations = np.where(diff_mask)
        changed_from = df1.values[difference_locations]
        changed_to = df2.values[difference_locations]
        return pd.DataFrame({'from': changed_from, 'to': changed_to},
                            index=changed.index)


def import_notes(notes_folder, backup=True, dry_run=False):
    """
    Opens a connection to the database, reads the DocumentNotes table,
    and overwrites entries with the contents of .md files in indir 
    """
    # Get relevant tables from database
    db = sqlite3.connect(DATABASE_LOC)
    table_name = 'DocumentNotes'
    notes = pd.read_sql_query("SELECT * from {}".format(table_name), db)
    if backup:
        notes.to_pickle('DocumentNotes.bkp.pkl')
    notes_orig = notes.copy()
    all_files = glob.glob(os.path.join(notes_folder, "*.md"))    
    for f in all_files:
        # Reading the file content to create a DataFrame
        with open(f, 'r') as ff:
            md_str = ff.read()
        file_name = os.path.splitext(os.path.basename(f))[0]
        doc_id = int(file_name.split('(', 1)[1].split(')', 1)[0])
        notes.loc[notes['documentId'] == doc_id, 'text'] = md_str
        notes.loc[notes['documentId'] == doc_id, 'baseNote'] = md_str

    md_inside_p = lambda x: markdown.markdown(x.replace('"', '&quot;')).\
                            replace('<br />','<br/>').replace('\n', '')[3:-4]
    notes['text'] = notes['text'].apply(md_inside_p)
    notes['baseNote'] = notes['baseNote'].apply(md_inside_p)
    
    if dry_run:
        print(diff_pd(notes_orig, notes))
    else:
        notes.to_sql(table_name, db, if_exists='replace', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
            '')
    parser.add_argument('notes_folder', type=str,
            help='Path to folder containing markdown notes')

    args = parser.parse_args()
    notes_folder = os.path.abspath(args.notes_folder)
    import_notes(notes_folder, backup=True, dry_run=True)
    
