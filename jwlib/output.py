import os
from sys import stderr
import re

pj = os.path.join

SAFE_FILE_NAMES = False


def _truncate_file(file, string=''):
    """Create a file and the parent directories."""
    d = os.path.dirname(file)
    os.makedirs(d, exist_ok=True)

    # Don't truncate non-empty files
    try:
        if os.stat(file).st_size != 0:
            return
    except FileNotFoundError:
        pass

    with open(file, 'w', encoding='utf-8') as f:
        f.write(string)


def output_stdout(categories, wd, uniq=False):
    """Output URLs or filenames to stdout.

    :param categories: A list generated by JWBroadcasting.parse()
    :param wd: Path to directory
    :param uniq: If True all output is unique, but unordered
    """
    out = []
    for category in categories:
        for item in category.content:
            if not item.iscategory:
                if item.file:
                    out.append(os.path.relpath(item.file, wd))
                else:
                    out.append(item.url)
    if uniq:
        out = set(out)

    print(*out, sep='\n')


def _write_to_m3u(source, name, file):
    """Write entry to a M3U playlist file."""
    _truncate_file(file, string='#EXTM3U\n')
    with open(file, 'a', encoding='utf-8') as f:
        f.write('#EXTINF:0,' + name + '\n' + source + '\n')
        

def output_m3u(categories, wd, subdir, writer=_write_to_m3u, flat=False, file_ending='.m3u'):
    """Create a M3U playlist tree.

    :param categories: A list generated by JWBroadcasting.parse()
    :param wd: Path to destination directory
    :param subdir: Name for the subdir where data will be saved
    :param writer: Function to write to files
    :param flat: If all playlist will be saved outside of subdir
    :param file_ending: Well, duh
    """
    for category in categories:

        if flat:
            # Flat mode, all files in working dir
            output_file = pj(wd, category.key + ' - ' + _filter_filename(category.name) + file_ending)
            source_prepend_dir = subdir
        elif category.home:
            # For home/index/starting categories
            # The current file gets saved outside the subdir
            # Links point inside the subdir
            source_prepend_dir = subdir
            output_file = pj(wd, _filter_filename(category.name) + file_ending)
        else:
            # For all other categories
            # Things get saved inside the subdir
            # No need to prepend links with the subdir itself
            source_prepend_dir = ''
            output_file = pj(wd, subdir, category.key + file_ending)

        # Since we want to start on a clean file, remove the old one
        try:
            os.remove(output_file)
        except FileNotFoundError:
            pass

        for item in category.content:
            if item.iscategory:
                if flat:
                    continue
                name = item.name.upper()
                source = pj('.', source_prepend_dir, item.key + file_ending)
            else:
                name = item.name
                if item.file:
                    source = pj('.', source_prepend_dir, os.path.basename(item.file))
                else:
                    source = item.url
            writer(source, name, output_file)


def _write_to_html(source, name, file):
    """Write a HTML file with a hyperlink to a media file."""
    _truncate_file(file, string='<!DOCTYPE html>\n<head><meta charset="utf-8" /></head>')
    with open(file, 'a', encoding='utf-8') as f:
        f.write('\n<a href="{0}">{1}</a><br>'.format(source, name))


def output_html(categories, wd, subdir):
    """Invokes output_m3u() with writer=_write_to_html and file_ending='.html')"""
    output_m3u(categories, wd, subdir, writer=_write_to_html, file_ending='.html')


def output_filesystem(categories, wd, subdir, include_keyname=False):
    """Creates a directory structure with symlinks to videos

    :param categories: A list generated by JWBroadcasting.parse()
    :param wd: Path to destination directory
    :param subdir: Name of subdir where data will be saved
    :param include_keyname: If categories will have keyname prepended
    """
    for category in categories:
        
        # Create the directory
        output_dir = pj(wd, subdir, category.key)
        os.makedirs(output_dir, exist_ok=True)

        # Index/starting/home categories: create link outside subdir
        if category.home:
            link = pj(wd, _filter_filename(category.name))
            # Note: the source will be relative
            source = pj(subdir, category.key)
            try:
                os.symlink(source, link)
            except FileExistsError:
                pass

        for item in category.content:

            if item.iscategory:
                d = pj(wd, subdir, item.key)
                os.makedirs(d, exist_ok=True)
                source = pj('..', item.key)

                if include_keyname:
                    link = pj(output_dir, item.key + ' - ' + _filter_filename(item.name))
                else:
                    link = pj(output_dir, _filter_filename(item.name))

            else:
                if not item.file:
                    continue

                source = pj('..', os.path.basename(item.file))
                ext = os.path.splitext(item.file)[1]
                link = pj(output_dir, _filter_filename(item.name + ext))

            try:
                os.symlink(source, link)
            except FileExistsError:
                pass


def _filter_filename(name):
    """Remove unsafe characters from file names"""

    if SAFE_FILE_NAMES:
        # NTFS/FAT forbidden characters
        regex = '[<>:"|?*/\\\\\0]'
    else:
        # Unix forbidden characters
        regex = '[/\\\\\0]'

    return re.sub(regex, '', name)


def clean_symlinks(d, clean_all=False, quiet=0):
    """Clean out broken symlinks from dir

    :param d: Path to directory to clean
    :param clean_all: Remove non-broken symlinks too
    :param quiet: Log level (int)
    """
    if not os.path.isdir(d):
        return

    for subdir in os.listdir(d):
            subdir = pj(d, subdir)
            if not os.path.isdir(subdir):
                continue

            for file in os.listdir(subdir):
                file = pj(subdir, file)
                if not os.path.islink(file):
                    continue

                source = pj(subdir, os.readlink(file))

                if clean_all or not os.path.exists(source):
                    if quiet < 2:
                        print('removing link: ' + os.path.basename(file), file=stderr)
                    os.remove(file)
