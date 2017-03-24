# mendeley-viz
Tools to extract notes from, and visualise mendeley libraries (currently only for UNIX)

## Install
Currently this is just one script: `export_notes.py`. To run it
you must install the python dependencies. It is recommended that
you simply create a new conda environment, activate it, and
run the script, like this:

### Quick start and test drive
```
git clone https://github.com/kungfujam/mendeley-viz.git
cd mendeley-viz
conda create -n mviz python=2 pandas
source activate mviz
pip install html2text
./export_notes.py -h
mkdir test
./export_notes.py test
ls test
```

## TODO
1. Write a script, `import_notes`, that does the reverse of `export_notes`, 
allowing users to edit notes externally and put them back in the database
1. Write visualization script that generates input for Gephi to visualize networks
  - Start by just making networks people and papers
  - Decide how to split into 'documents' and 'entities'...
