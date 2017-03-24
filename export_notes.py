#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reads the mendeley sqlite database and extracts notes as .md files to 
a given folder.
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
import sys
import html2text
import csv
import argparse

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


def export_notes(outdir, folder=None):
    """
    Reads the mendeley sqlite database and extracts notes as .md
    files to a given folder. This is intended to allow users of
    Mendeley to write notes in the GUI, but export them to a
    version controlled github repo folder for easy viewing.
    """
    # Get relevant tables from database
    db = sqlite3.connect(DATABASE_LOC)
    table_name = 'Documents'
    documents = pd.read_sql_query("SELECT * from {}".format(table_name), db)
    table_name = 'DocumentNotes'
    notes = pd.read_sql_query("SELECT * from {}".format(table_name), db)
    table_name = 'Folders'
    folders = pd.read_sql_query("SELECT * from {}".format(table_name), db)
    table_name = 'DocumentFolders'
    docfolders = pd.read_sql_query("SELECT * from {}".format(table_name), db)
        
    # get notes from required mendeley folder
    if folder is not None:
        assert folder in folders['name'].values, \
            "Folder name [{}] not found. ".format(folder) + \
            "Check name matches folder name in the Mendeley GUI exactly."
        folders_ = folders.loc[folders['name'] == folder, ['id', 'name']]
        folders_.rename(columns={'id': 'folderId', 'name': 'folderName'}, 
                        inplace=True)
        docfolders_ = pd.merge(docfolders, folders_)
        notes_ = pd.merge(notes, docfolders_)
    else:
        notes_ = notes
    
    # Get document level information    
    notes_['mdText'] = notes_['text'].apply(html2text.html2text)
    notes_.rename(columns={'id': 'noteId'}, inplace=True)
    notes__ = pd.merge(notes_, 
                       documents[['id', 'title', 'citationKey']].\
                           rename(columns={'id': 'documentId'}))
    
    # Export each note to a .md file
    for name, group in notes__.groupby('noteId'):
        fn = doc_name_str.format(
                citationKey=group['citationKey'].values[0],
                docid=group['documentId'].values[0],
                title=group['title'].values[0])
        out = '{}{}{}.md'.format(outdir, os.sep, fn)
        # This was the only way I found to avoid the single field
        # being exported wrapped in quotes. It will introduce additional spaces
        group.to_csv(
                out,
                columns=['mdText'],
                index=False,
                quoting=csv.QUOTE_NONE, 
                header=False, 
                escapechar=' ',
                encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
            'Reads the mendeley sqlite database and extracts notes as .md '
            'files to a given folder. This is intended to allow users of '
            'Mendeley to write notes in the GUI, but export them to a '
            'version controlled github repo folder for easy viewing. '
            'Markdown files will be named in the following format: '
            '\n\n\t"{}".'.format(doc_name_str))
    parser.add_argument('outdir', type=str,
            help='Target folder to save the outputs. Must already exist!')
    parser.add_argument('-f', '--folder', type=str, default=None, nargs=1,
            help='Name of the Mendeley folder to extract notes from. '
            'If ommited, all notes will be exported.')

    args = parser.parse_args()
    outdir = os.path.abspath(args.outdir)
    folder = args.folder
    export_notes(outdir, folder)
    